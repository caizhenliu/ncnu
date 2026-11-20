from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection

router = APIRouter(prefix="/api/schedules", tags=["Schedule 課程排課模組"])

TEACHER_DIRECTORY = [
    "王育民",
    "司馬添",
    "白炳豐",
    "余菁蓉",
    "林妙聰",
    "侯宏彬",
    "姜美玲",
    "洪嘉良",
    "高竹諠",
    "陳小芬",
    "陳建宏",
    "陳彥錚",
    "游子宜",
    "黃俊哲",
    "練莊明",
    "鄭育評",
    "戴榮賦",
    "簡宏宇",
    "龔榮發",
]

DEPARTMENTS = [
    "經濟學系",
    "國際企業學系",
    "資訊管理學系",
    "財務金融學系",
    "高階經營管理碩士學位學程",
    "觀光休閒與餐旅管理學系觀光",
    "觀光休閒與餐旅管理學系餐旅",
    "兩岸高階主管經營管理境外碩士在職學位學程",
    "新興產業策略與發展博士學位學程",
    "新興產業策略與發展碩士學位學程",
    "區域發展重點產業碩士專班",
    "管理學院學士班",
    "管理學院商業管理及資訊科技創新應用全英語碩士學位學程",
    "管理學院",
]

SCHEDULE_ROOM_CODES = {
    "M112",
    "M113",
    "M115",
    "M203",
    "M204",
    "M206",
    "M207",
    "M210",
    "M212",
    "M213",
    "M215",
    "M217",
    "M226",
    "M228",
    "M241",
    "M251",
    "M253",
    "M255",
    "M260",
    "M268",
    "M312",
    "M320",
    "M350",
    "M432",
    "M443",
    "M451",
    "M457",
}

class CourseCreate(BaseModel):
    course_name: str
    teacher_id: int
    room_id: Optional[int] = None
    day_of_week: int
    start_time: str
    end_time: str
    schedule_status: str = "requested"

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    teacher_id: Optional[int] = None
    room_id: Optional[int] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    schedule_status: Optional[str] = None

# 取得前端下拉選單需要的教室與已核准老師清單
@router.get("/options")
def get_schedule_options():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT room_id, room_code, room_name FROM rooms WHERE is_active = TRUE ORDER BY room_code")
            rooms = cur.fetchall()

            cur.execute(
                """
                SELECT user_id, full_name
                FROM users
                WHERE role = 'teacher' AND account_status = 'approved'
                ORDER BY user_id
                """
            )
            teachers = cur.fetchall()

    information_management_teachers = list(TEACHER_DIRECTORY)
    information_management_teachers.extend(
        teacher["full_name"]
        for teacher in teachers
        if teacher["full_name"] not in information_management_teachers
    )
    teachers_by_department = {
        department: information_management_teachers if department == "資訊管理學系" else []
        for department in DEPARTMENTS
    }
    return {
        "rooms": rooms,
        "schedule_rooms": [
            room for room in rooms
            if room["room_code"] in SCHEDULE_ROOM_CODES
        ],
        "teachers": teachers,
        "departments": DEPARTMENTS,
        "teachers_by_department": teachers_by_department,
    }

# 取得所有排課清單（同時把時間格式化為 HH:MM:SS 字串給前端 FullCalendar）
@router.get("/courses")
def get_all_courses():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    course_id,
                    course_name,
                    teacher_id,
                    room_id,
                    day_of_week,
                    TO_CHAR(start_time, 'HH24:MI:SS') AS start_time,
                    TO_CHAR(end_time, 'HH24:MI:SS') AS end_time,
                    schedule_status
                FROM courses
                ORDER BY day_of_week ASC, start_time ASC
                """
            )
            return cur.fetchall()

# 新增排課
@router.post("/courses")
def create_course(data: CourseCreate):
    if not (1 <= data.day_of_week <= 7):
        raise HTTPException(status_code=400, detail="星期必須介於 1 到 7 之間")
    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="結束時間必須晚於開始時間")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO courses (course_name, teacher_id, room_id, day_of_week, start_time, end_time, schedule_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING course_id
                """,
                (data.course_name, data.teacher_id, data.room_id, data.day_of_week, data.start_time, data.end_time, data.schedule_status)
            )
            new_id = cur.fetchone()["course_id"]
            conn.commit()

    return {"message": "排課新增成功", "course_id": new_id}

# 修改排課（支援表單完整修改，也支援管理員滑鼠 Drag & Drop 僅傳送 day_of_week, start_time, end_time）
@router.put("/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdate):
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="沒有提供任何需要更新的欄位")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            set_clauses = [f"{col} = %s" for col in fields.keys()]
            values = list(fields.values()) + [course_id]

            cur.execute(
                f"""
                UPDATE courses
                SET {', '.join(set_clauses)}
                WHERE course_id = %s
                RETURNING course_id
                """,
                values
            )
            updated = cur.fetchone()
            conn.commit()

    if not updated:
        raise HTTPException(status_code=404, detail="找不到該筆課程資料")
    return {"message": "排課更新成功", "course_id": course_id}

# 刪除排課
@router.delete("/courses/{course_id}")
def delete_course(course_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM courses WHERE course_id = %s RETURNING course_id", (course_id,))
            deleted = cur.fetchone()
            conn.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="找不到該筆課程資料")
    return {"message": "排課已刪除", "course_id": course_id}