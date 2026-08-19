from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.database import get_db
from app.routes.dashboard import get_current_user

router = APIRouter()

def require_auth(request: Request):
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/api/students")
async def get_students(request: Request, _: None = Depends(require_auth)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT roll_number, name, registered_at FROM students")
        return [dict(row) for row in cursor.fetchall()]

@router.get("/api/attendance/{date}")
async def get_attendance(request: Request, date: str, _: None = Depends(require_auth)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.roll_number, s.name, a.marked_at 
            FROM attendance a 
            JOIN students s ON a.student_id = s.id 
            JOIN sessions sess ON a.session_id = sess.id
            WHERE sess.date = ?
        ''', (date,))
        return [dict(row) for row in cursor.fetchall()]

@router.get("/api/stats")
async def get_stats(request: Request, _: None = Depends(require_auth)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM students")
        total_students = cursor.fetchone()['count']
        
        # Today's session
        cursor.execute("SELECT id FROM sessions WHERE is_active = 1 LIMIT 1")
        active_session = cursor.fetchone()
        
        todays_count = 0
        if active_session:
            cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE session_id = ?", (active_session['id'],))
            todays_count = cursor.fetchone()['count']
            
        overall_percentage = 0
        if total_students > 0:
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            total_sessions = cursor.fetchone()['count']
            
            if total_sessions > 0:
                cursor.execute("SELECT COUNT(*) as count FROM attendance")
                total_attendance = cursor.fetchone()['count']
                overall_percentage = (total_attendance / (total_students * total_sessions)) * 100
                
        return {
            "total_students": total_students,
            "todays_count": todays_count,
            "overall_attendance_percent": round(overall_percentage, 2)
        }
