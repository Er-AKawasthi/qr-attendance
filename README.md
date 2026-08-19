# 🎓 QR Attendance System — IIIT Allahabad
### Course: AI Tools for Research

A real-time, anti-proxy QR attendance system. Professor opens a stunning dashboard on the digital board, students scan the dynamic QR from their phones to mark attendance. QR refreshes every 20 seconds — screenshots become useless!

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
# Copy the example env file
cp .env.example .env

# Edit with your settings
# PROFESSOR_PASSWORD=your_secure_password  (default: admin123)
# BASE_URL=https://your-app.onrender.com   (default: http://localhost:8000)
```

### 3. Run the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open Dashboard
- Go to `http://localhost:8000` in your browser
- Login with your professor password (default: `admin123`)
- Click **Start Session** to begin attendance
- Display the dashboard on the digital board/projector
- Students scan the QR code from their phones!

---

## 📱 How It Works

### For Professor
1. Open the dashboard URL on the classroom digital board
2. Login with your password
3. Click **Start Session** → A dynamic QR code appears
4. QR refreshes every 20 seconds automatically
5. Watch live as students scan and attendance count goes up
6. Click **Stop Session** when done → attendance syncs to Google Sheets

### For Students
1. Scan the QR code on the board with your phone camera
2. Enter your roll number
3. First time? Enter your name too (auto-registered for future classes)
4. ✅ Attendance marked!

### Anti-Proxy Security
- QR code changes every **20 seconds** with a new UUID token
- If someone screenshots and shares — the QR is already expired
- Each student can only mark **once per session** (duplicate prevention)
- Only the **current token** is valid at any time

---

## 🌐 Deployment on Render.com (Free)

1. Push this code to a GitHub repository
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set environment variables:
   - `PROFESSOR_PASSWORD` = your secure password
   - `SECRET_KEY` = any random string
   - `BASE_URL` = `https://your-app-name.onrender.com`
5. Deploy! Your app will be live with HTTPS.

---

## 📊 Google Sheets Integration (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable Google Sheets API
3. Create a Service Account → Download `credentials.json`
4. Place `credentials.json` in the project root
5. Create a Google Sheet and share it with the service account email
6. Set environment variables:
   ```
   GOOGLE_SHEETS_ENABLED=true
   GOOGLE_SHEETS_ID=your_sheet_id_here
   ```

The sheet auto-populates with:
| Roll No | Name | 19-Aug | 20-Aug | ... |
|---------|------|--------|--------|-----|
| IIT2024001 | Amit | P | A | ... |

---

## 📁 Project Structure

```
qr-attendance/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Settings & env variables
│   ├── database.py           # SQLite DB setup
│   ├── qr_engine.py          # Dynamic QR token manager
│   ├── sheets_sync.py        # Google Sheets integration
│   ├── routes/
│   │   ├── dashboard.py      # Professor dashboard + WebSocket
│   │   ├── attendance.py     # Student attendance API
│   │   └── admin.py          # Admin stats API
│   ├── templates/
│   │   ├── login.html        # Professor login
│   │   ├── dashboard.html    # Main dashboard (projector view)
│   │   └── mark.html         # Student form (mobile)
│   └── static/
│       ├── css/dashboard.css  # All styles
│       └── js/dashboard.js   # WebSocket + live updates
├── requirements.txt
├── render.yaml               # Render.com config
├── .env.example              # Environment template
└── .gitignore
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.10 + FastAPI |
| Database | SQLite |
| Real-time | WebSocket |
| QR Code | qrcode + Pillow |
| Frontend | HTML/CSS/JS (Jinja2) |
| Sheets | gspread |
| Deployment | Render.com |

---

Built with ❤️ for IIIT Allahabad
