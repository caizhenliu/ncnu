"""
模組一：管院空間查詢模組
- 不須登入：查詢、瀏覽教室資料（含 360 全景、平面圖位置）
- 管理員：新增、修改、刪除教室資料
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from database import get_db_connection

router = APIRouter(prefix="/api/rooms", tags=["Rooms 管院空間查詢模組"])

ROOM_COLUMNS = """
    room_id, room_code, room_name, floor, capacity, equipment,
    panorama_url, map_x, map_y, is_active, updated_at
"""


class RoomBase(BaseModel):
    room_code: str = Field(..., min_length=1, max_length=20)
    room_name: str = Field(..., min_length=1, max_length=100)
    floor: str = Field(..., min_length=1, max_length=20)
    capacity: int = Field(40, ge=0)
    equipment: Optional[str] = None
    panorama_url: Optional[str] = Field(None, max_length=255)
    map_x: Optional[float] = Field(None, ge=0, le=100)
    map_y: Optional[float] = Field(None, ge=0, le=100)
    is_active: bool = True


class RoomUpdate(BaseModel):
    room_code: Optional[str] = Field(None, min_length=1, max_length=20)
    room_name: Optional[str] = Field(None, min_length=1, max_length=100)
    floor: Optional[str] = Field(None, min_length=1, max_length=20)
    capacity: Optional[int] = Field(None, ge=0)
    equipment: Optional[str] = None
    panorama_url: Optional[str] = Field(None, max_length=255)
    map_x: Optional[float] = Field(None, ge=0, le=100)
    map_y: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


def require_admin(user_id: Optional[int]):
    """確認呼叫者是已審核通過的管理員（前端以 X-User-Id 標頭帶入登入者 ID）"""
    if user_id is None:
        raise HTTPException(status_code=401, detail="請先以管理員帳號登入")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role, account_status FROM users WHERE user_id = %s",
                (user_id,),
            )
            user = cur.fetchone()
    if not user or user["role"] != "admin" or user["account_status"] != "approved":
        raise HTTPException(status_code=403, detail="只有管理員可以增刪修改教室資料")


# ---------- 公開查詢（不須登入） ----------

@router.get("")
def list_rooms(
    floor: Optional[str] = None,
    keyword: Optional[str] = None,
    min_capacity: Optional[int] = None,
    include_inactive: bool = False,
):
    conditions, params = [], []
    if not include_inactive:
        conditions.append("is_active = TRUE")
    if floor:
        conditions.append("floor = %s")
        params.append(floor)
    if keyword:
        conditions.append("(room_code ILIKE %s OR room_name ILIKE %s OR equipment ILIKE %s)")
        like = f"%{keyword}%"
        params += [like, like, like]
    if min_capacity:
        conditions.append("capacity >= %s")
        params.append(min_capacity)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {ROOM_COLUMNS} FROM rooms {where} ORDER BY floor, room_code", params)
            return cur.fetchall()


@router.get("/floors")
def list_floors():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT floor FROM rooms WHERE is_active = TRUE ORDER BY floor")
            return [row["floor"] for row in cur.fetchall()]


@router.get("/{room_id}")
def get_room(room_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {ROOM_COLUMNS} FROM rooms WHERE room_id = %s", (room_id,))
            room = cur.fetchone()
    if not room:
        raise HTTPException(status_code=404, detail="找不到這間教室")
    return room


# ---------- 管理員專用 ----------

@router.post("", status_code=201)
def create_room(data: RoomBase, x_user_id: Optional[int] = Header(None)):
    require_admin(x_user_id)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM rooms WHERE room_code = %s", (data.room_code,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail=f"教室編號 {data.room_code} 已存在")
            cur.execute(
                f"""
                INSERT INTO rooms (room_code, room_name, floor, capacity, equipment,
                                   panorama_url, map_x, map_y, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {ROOM_COLUMNS}
                """,
                (data.room_code, data.room_name, data.floor, data.capacity, data.equipment,
                 data.panorama_url, data.map_x, data.map_y, data.is_active),
            )
            room = cur.fetchone()
        conn.commit()
    return room


@router.put("/{room_id}")
def update_room(room_id: int, data: RoomUpdate, x_user_id: Optional[int] = Header(None)):
    require_admin(x_user_id)
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="沒有要更新的欄位")

    sets = ", ".join(f"{k} = %s" for k in fields) + ", updated_at = CURRENT_TIMESTAMP"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if "room_code" in fields:
                cur.execute(
                    "SELECT 1 FROM rooms WHERE room_code = %s AND room_id <> %s",
                    (fields["room_code"], room_id),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"教室編號 {fields['room_code']} 已存在")
            cur.execute(
                f"UPDATE rooms SET {sets} WHERE room_id = %s RETURNING {ROOM_COLUMNS}",
                [*fields.values(), room_id],
            )
            room = cur.fetchone()
        conn.commit()
    if not room:
        raise HTTPException(status_code=404, detail="找不到這間教室")
    return room


@router.delete("/{room_id}")
def delete_room(room_id: int, x_user_id: Optional[int] = Header(None)):
    require_admin(x_user_id)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 其他模組（排課、借用）還有引用時，不直接刪除，避免破壞別人的資料
            cur.execute("SELECT COUNT(*) AS n FROM courses WHERE room_id = %s", (room_id,))
            used_by_courses = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM bookings WHERE room_id = %s", (room_id,))
            used_by_bookings = cur.fetchone()["n"]
            if used_by_courses or used_by_bookings:
                raise HTTPException(
                    status_code=409,
                    detail=f"此教室仍有 {used_by_courses} 筆排課、{used_by_bookings} 筆借用紀錄，"
                           "請改為「停用」而不是刪除",
                )
            cur.execute("DELETE FROM rooms WHERE room_id = %s RETURNING room_id", (room_id,))
            deleted = cur.fetchone()
        conn.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="找不到這間教室")
    return {"message": "已刪除", "room_id": room_id}
