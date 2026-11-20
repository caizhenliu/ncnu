from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import router as auth
import schedule
import rooms

app = FastAPI(title="1151 軟體工程學期專案 - 管院空間與排課系統")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(schedule.router)
app.include_router(rooms.router)

# 靜態檔案（360 全景照片等）
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("schedule.html")

@app.get("/rooms")
def serve_rooms_page():
    # 模組一：管院空間查詢（不須登入即可瀏覽）
    return FileResponse("rooms.html")
