from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

from app.database import init_db
from app.qr_engine import QREngine
from app.routes import dashboard, attendance, admin

# Resolve paths relative to this file
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="QR Attendance System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(dashboard.router)
app.include_router(attendance.router)
app.include_router(admin.router)

@app.on_event("startup")
async def startup_event():
    init_db()
    app.state.qr_engine = QREngine()

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")
