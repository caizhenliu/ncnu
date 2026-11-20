from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["Auth 共用帳號"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password_hash: str
    full_name: str
    email: str
    role: str = "student"

class ReviewUserRequest(BaseModel):
    account_status: str  # 'approved' 或 'rejected'

@router.post("/login")
def login(data: LoginRequest):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username, full_name, email, role, account_status
                FROM users
                WHERE username = %s AND password_hash = %s
                """,
                (data.username, data.password)
            )
            user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤！")
    if user["account_status"] == "pending":
        raise HTTPException(status_code=403, detail="您的帳號尚在「待管理員審核」中，請通過後再登入！")
    if user["account_status"] == "rejected":
        raise HTTPException(status_code=403, detail="您的帳號申請已被退件，請聯繫系統管理員。")

    return user

@router.post("/register")
def register(data: RegisterRequest):
    if data.role not in ("teacher", "student"):
        raise HTTPException(status_code=400, detail="註冊身分僅限 teacher 或 student")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM users WHERE username = %s OR email = %s",
                (data.username, data.email)
            )
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="此帳號或 Email 已被註冊！")

            cur.execute(
                """
                INSERT INTO users (username, password_hash, full_name, email, role, account_status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
                RETURNING user_id, username, full_name, role, account_status
                """,
                (data.username, data.password_hash, data.full_name, data.email, data.role)
            )
            new_user = cur.fetchone()
            conn.commit()

    return new_user

@router.get("/pending-users")
def get_pending_users():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username, full_name, email, role, account_status
                FROM users
                WHERE account_status = 'pending'
                ORDER BY created_at ASC
                """
            )
            return cur.fetchall()

@router.put("/users/{user_id}/review")
def review_user(user_id: int, data: ReviewUserRequest):
    if data.account_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="審核狀態無效")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET account_status = %s
                WHERE user_id = %s
                RETURNING user_id, username, full_name, role, account_status
                """,
                (data.account_status, user_id)
            )
            updated = cur.fetchone()
            conn.commit()

    if not updated:
        raise HTTPException(status_code=404, detail="找不到該使用者")
    return updated