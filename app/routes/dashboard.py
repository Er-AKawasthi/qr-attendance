from fastapi import APIRouter, Request, Response, Depends, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from app.config import PROFESSOR_PASSWORD, SECRET_KEY, QR_REFRESH_INTERVAL, BASE_URL
from app.database import get_db
from pathlib import Path
import asyncio
import datetime

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
signer = TimestampSigner(SECRET_KEY)

def get_current_user(request: Request):
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        data = signer.unsign(token, max_age=86400).decode()
        if data == "authenticated=true":
            return True
    except (BadSignature, SignatureExpired):
        pass
    return None

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_post(request: Request, password: str = Form(...)):
    if password == PROFESSOR_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session", value=signer.sign("authenticated=true").decode(), httponly=True)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.post("/api/session/start")
async def start_session(request: Request):
    if not get_current_user(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    qr_engine = request.app.state.qr_engine
    
    with get_db() as conn:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (date, is_active) VALUES (?, 1)", (date_str,))
        session_id = cursor.lastrowid
        conn.commit()
        
    qr_engine.start_session(session_id)
    return {"status": "started", "session_id": session_id}

@router.post("/api/session/stop")
async def stop_session(request: Request):
    if not get_current_user(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    qr_engine = request.app.state.qr_engine
    sheets_sync = request.app.state.sheets_sync
    
    session_id = qr_engine.session_id
    qr_engine.stop_session()
    
    if session_id:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET is_active = 0, ended_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
            conn.commit()
            
            # Sync to sheets
            cursor.execute("SELECT date FROM sessions WHERE id = ?", (session_id,))
            date_str = cursor.fetchone()['date']
            
            cursor.execute("SELECT roll_number, name FROM students")
            all_students = cursor.fetchall()
            
            cursor.execute('''
                SELECT s.roll_number 
                FROM attendance a 
                JOIN students s ON a.student_id = s.id 
                WHERE a.session_id = ?
            ''', (session_id,))
            present_rolls = {row['roll_number'] for row in cursor.fetchall()}
            
            sync_data = []
            for student in all_students:
                sync_data.append({
                    "roll_number": student['roll_number'],
                    "name": student['name'],
                    "present": student['roll_number'] in present_rolls
                })
                
        # Optional: Run in background
        asyncio.create_task(asyncio.to_thread(sheets_sync.sync_attendance, date_str, sync_data))
            
    return {"status": "stopped"}

@router.websocket("/ws/qr")
async def websocket_qr(websocket: WebSocket):
    await websocket.accept()
    qr_engine = websocket.app.state.qr_engine
    
    async def on_attendance(student_info):
        try:
            await websocket.send_json({"type": "attendance", "data": student_info})
        except:
            pass

    qr_engine.callbacks.append(on_attendance)
    
    try:
        while True:
            if qr_engine.session_active:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM students")
                    total_students = cursor.fetchone()['count']
                    
                    cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE session_id = ?", (qr_engine.session_id,))
                    attendance_count = cursor.fetchone()['count']
                    
                    cursor.execute('''
                        SELECT s.roll_number, s.name, a.marked_at 
                        FROM attendance a 
                        JOIN students s ON a.student_id = s.id 
                        WHERE a.session_id = ? 
                        ORDER BY a.marked_at DESC LIMIT 5
                    ''', (qr_engine.session_id,))
                    recent = [dict(row) for row in cursor.fetchall()]
                    
                time_elapsed = (datetime.datetime.now() - qr_engine.token_created_at).total_seconds()
                expires_in = max(0, int(QR_REFRESH_INTERVAL - time_elapsed))
                
                if expires_in <= 0:
                    qr_engine.refresh_token()
                    expires_in = QR_REFRESH_INTERVAL
                    
                state = qr_engine.get_state(BASE_URL, expires_in, attendance_count, total_students, recent)
                await websocket.send_json({"type": "state", "data": state})
            else:
                await websocket.send_json({"type": "state", "data": {"session_active": False}})
                
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        if on_attendance in qr_engine.callbacks:
            qr_engine.callbacks.remove(on_attendance)
