from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

class MarkAttendanceRequest(BaseModel):
    token: str
    roll_number: str
    name: Optional[str] = None

@router.get("/mark/{token}", response_class=HTMLResponse)
async def mark_get(request: Request, token: str):
    qr_engine = request.app.state.qr_engine
    if not qr_engine.is_token_valid(token):
        return HTMLResponse("<h1>Invalid or Expired Token</h1>", status_code=400)
    
    return templates.TemplateResponse(request=request, name="mark.html", context={"token": token})

@router.post("/api/mark")
async def mark_post(request: Request, data: MarkAttendanceRequest):
    qr_engine = request.app.state.qr_engine
    
    if not qr_engine.is_token_valid(data.token):
        return JSONResponse({"error": "Invalid or expired token"}, status_code=400)
        
    session_id = qr_engine.session_id
    roll_number = data.roll_number.strip().upper()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,))
        student = cursor.fetchone()
        
        if not student:
            if not data.name:
                return JSONResponse({"needs_registration": True})
            
            cursor.execute("INSERT INTO students (roll_number, name) VALUES (?, ?)", (roll_number, data.name.strip()))
            student_id = cursor.lastrowid
            student_name = data.name.strip()
        else:
            student_id = student['id']
            student_name = student['name']
            
        # Check if already marked
        cursor.execute("SELECT * FROM attendance WHERE student_id = ? AND session_id = ?", (student_id, session_id))
        if cursor.fetchone():
            return {"status": "already_marked", "message": f"Attendance already marked for {student_name}"}
            
        cursor.execute("INSERT INTO attendance (student_id, session_id) VALUES (?, ?)", (student_id, session_id))
        conn.commit()
        
    # Notify dashboard
    await qr_engine.notify_attendance({
        "roll_number": roll_number,
        "name": student_name,
        "time": "Just now"
    })
    
    return {"status": "success", "message": f"Attendance marked for {student_name}", "name": student_name}
