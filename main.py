from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import router as auth
import schedule

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

@app.get("/")
def serve_frontend():
    return FileResponse("schedule.html")