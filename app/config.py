import os
import socket
import secrets
from dotenv import load_dotenv

load_dotenv()

COURSE_NAME = 'AI Tools for Research'
QR_REFRESH_INTERVAL = 60  # seconds
PROFESSOR_PASSWORD = os.getenv('PROFESSOR_PASSWORD', 'admin123')
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./attendance.db')
GOOGLE_SHEETS_ENABLED = os.getenv('GOOGLE_SHEETS_ENABLED', 'false').lower() == 'true'
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')

def _get_local_ip():
    """Auto-detect the machine's LAN IP so phones on the same network can connect."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'localhost'

BASE_URL = os.getenv('BASE_URL', f'http://{_get_local_ip()}:8000')
