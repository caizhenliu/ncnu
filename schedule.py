from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from database import get_db_connection
from sessions import get_session

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

TOURISM_TEACHER_DIRECTORY = [
    "黃裕智",
    "鄭健雄",
    "戴有德",
    "林士彥",
    "楊明青",
    "丁冰和",
    "曾永平",
    "葉明亮",
    "曾喜鵬",
    "吳淑玲",
    "蔡宗伯",
    "龎鳳嫺",
    "伊香紅実",
    "林國華",
    "潘岱儒",
    "陳國明",
    "陳信村",
    "陳瓊惠",
    "宋承先",
    "陳子洋",
    "莊雅婷",
    "龎龍",
    "江侑姿",
]

DEPARTMENT_TEACHER_DIRECTORY = {
    "經濟學系": [
        "陳建良",
        "欉清全",
        "陳江明",
        "葉家瑜",
        "邱顯鴻",
        "林佑龍",
        "張德存",
        "花國庭",
    ],
    "國際企業學系": [
        "許秋萍",
        "施信佑",
        "王銘杰",
        "胡毓彬",
        "林欣美",
        "駱世民",
        "陳靜怡",
        "莊文彬",
        "吳淑貞",
        "許文忠",
        "張玉芳",
        "佘日新",
        "黃鴻鈞",
        "梅筱珍",
        "余建明",
        "李巧琳",
        "董美戀",
        "康建民",
        "蔣豐維",
    ],
    "財務金融學系": [
        "賴雨聖",
        "柯冠成",
        "洪碧霞",
        "王健安",
        "戴維芯",
        "張榮顯",
        "葉家維",
        "蘇昱翔",
        "廖振傑",
        "郭憲章",
        "蔣淑芬",
        "謝東昇",
        "詹益錦",
        "陳秀椿",
    ],
    "觀光休閒與餐旅管理學系觀光": TOURISM_TEACHER_DIRECTORY,
    "觀光休閒與餐旅管理學系餐旅": TOURISM_TEACHER_DIRECTORY,
}

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

def get_current_schedule_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="請先登入")

    user = get_session(authorization[7:])
    if not user:
        raise HTTPException(status_code=401, detail="登入工作階段已失效，請重新登入")
    if user["role"] not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="此功能僅限管理員與教師使用")
    return user

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
        department: (
            information_management_teachers
            if department == "資訊管理學系"
            else DEPARTMENT_TEACHER_DIRECTORY.get(department, [])
        )
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
def get_all_courses(current_user: dict = Depends(get_current_schedule_user)):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
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
            """
            if current_user["role"] == "admin":
                cur.execute(f"{query} ORDER BY day_of_week ASC, start_time ASC")
            else:
                cur.execute(
                    f"{query} WHERE teacher_id = %s ORDER BY day_of_week ASC, start_time ASC",
                    (current_user["user_id"],)
                )
            return cur.fetchall()

# 新增排課
@router.post("/courses")
def create_course(data: CourseCreate, current_user: dict = Depends(get_current_schedule_user)):
    if not (1 <= data.day_of_week <= 7):
        raise HTTPException(status_code=400, detail="星期必須介於 1 到 7 之間")
    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="結束時間必須晚於開始時間")
    if current_user["role"] != "admin" and data.teacher_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="教師只能新增自己的課程")

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
def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: dict = Depends(get_current_schedule_user)
):
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="沒有提供任何需要更新的欄位")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_id FROM courses WHERE course_id = %s", (course_id,))
            course = cur.fetchone()
            if not course:
                raise HTTPException(status_code=404, detail="找不到該筆課程資料")
            if current_user["role"] != "admin":
                if course["teacher_id"] != current_user["user_id"]:
                    raise HTTPException(status_code=403, detail="教師只能修改自己的課程")
                if fields.get("teacher_id", current_user["user_id"]) != current_user["user_id"]:
                    raise HTTPException(status_code=403, detail="教師不能更改課程的授課老師")

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
def delete_course(course_id: int, current_user: dict = Depends(get_current_schedule_user)):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_id FROM courses WHERE course_id = %s", (course_id,))
            course = cur.fetchone()
            if not course:
                raise HTTPException(status_code=404, detail="找不到該筆課程資料")
            if current_user["role"] != "admin" and course["teacher_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="教師只能刪除自己的課程")

            cur.execute("DELETE FROM courses WHERE course_id = %s RETURNING course_id", (course_id,))
            deleted = cur.fetchone()
            conn.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="找不到該筆課程資料")
    return {"message": "排課已刪除", "course_id": course_id}