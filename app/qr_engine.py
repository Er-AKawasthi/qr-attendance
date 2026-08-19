import uuid
import datetime
import qrcode
import io
import base64
from typing import Optional

class QREngine:
    def __init__(self):
        self.current_token: str = ""
        self.token_created_at: Optional[datetime.datetime] = None
        self.session_active: bool = False
        self.session_id: Optional[int] = None
        self.callbacks = []

    def start_session(self, session_id: int):
        self.session_id = session_id
        self.session_active = True
        self.refresh_token()

    def stop_session(self):
        self.session_active = False
        self.session_id = None
        self.current_token = ""

    def refresh_token(self):
        if self.session_active:
            self.current_token = str(uuid.uuid4())
            self.token_created_at = datetime.datetime.now()

    def is_token_valid(self, token: str) -> bool:
        if not self.session_active or token != self.current_token:
            return False
        # Optional: check expiration (e.g. within 25 seconds allowing 5s grace period)
        if self.token_created_at:
            delta = datetime.datetime.now() - self.token_created_at
            if delta.total_seconds() > 25:
                return False
        return True

    def get_qr_image_base64(self, base_url: str) -> str:
        if not self.session_active:
            return ""
        url = f"{base_url}/mark/{self.current_token}"
        qr = qrcode.QRCode(
            version=4,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def get_state(self, base_url: str, expires_in: int, attendance_count: int, total_students: int, recent: list) -> dict:
        return {
            "qr_base64": self.get_qr_image_base64(base_url) if self.session_active else "",
            "token": self.current_token,
            "expires_in": expires_in,
            "attendance_count": attendance_count,
            "total_students": total_students,
            "recent": recent,
            "session_active": self.session_active
        }

    async def notify_attendance(self, student_info: dict):
        for callback in self.callbacks:
            await callback(student_info)
