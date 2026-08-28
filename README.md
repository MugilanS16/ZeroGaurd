# ZeroGuard AI — Cybercrime Reporting & Threat Intelligence Platform

ZeroGuard AI is a full-stack cybercrime reporting and automated incident classification system with real-time AI assistance, dynamic legal question generation, official complaint PDF drafting, and comprehensive user activity audit logging.

---

## 🏛️ Architecture & Tech Stack
- **Frontend**: React SPA built on Vite, React Router, Axios with JWT interceptors, and Recharts telemetry dashboards (`/frontend`).
- **Backend**: Python Flask REST API with SQLite (`cybercrime.db`), Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Migrate, and Flask-CORS (`app.py`).
- **AI Engine**: Gemini AI / Rule-based incident classifier and dynamic question generation engine (`/ai`).
- **Audit System**: Real-time user action tracking (`activity_logs`) and authentication security monitoring (`login_history`).

---

## 🚀 Running the Project

### 1. Start the Flask Backend (Port 5000)
```powershell
python app.py
```

### 2. Start the Vite React Frontend (Port 5173)
```powershell
cd frontend
npm run dev
```

### 3. Demo Credentials
- **Citizen Account**: `citizen@cybercrime.gov.in` / `CitizenPass123!`
- **Admin Account**: `admin@cybercrime.gov.in` / `AdminPass123!`
- **Google SSO Test**: `google.user@cybercrime.gov.in`
- **DigiLocker Test**: `digilocker.user@cybercrime.gov.in`

---

## 🔍 Database Migrations with Flask-Migrate

The database schema includes `users`, `complaints`, `activity_logs`, and `login_history`. To manage schema migrations:

```powershell
# 1. Initialize migration repository (one-time setup)
python -m flask db init

# 2. Generate a migration script after changing models in database/models.py
python -m flask db migrate -m "Describe your schema changes"

# 3. Apply the migration to cybercrime.db
python -m flask db upgrade
```

---

## 📊 Inspecting the Activity Log via SQLite3 CLI

You can inspect the database directly using the SQLite CLI or Python SQLite shell:

### Option A: Using SQLite CLI
```powershell
sqlite3 instance/cybercrime.db
```

#### Useful Audit Queries:
```sql
-- View latest 10 user activities
SELECT id, user_id, action_type, description, ip_address, timestamp 
FROM activity_logs 
ORDER BY timestamp DESC 
LIMIT 10;

-- Check all failed login attempts
SELECT id, user_id, login_method, ip_address, success, timestamp 
FROM login_history 
WHERE success = 0 
ORDER BY timestamp DESC;

-- Identify IPs with suspicious failed logins
SELECT ip_address, count(*) AS failed_count 
FROM login_history 
WHERE success = 0 
GROUP BY ip_address 
HAVING count(*) >= 3;

-- View activity distribution by action type
SELECT action_type, count(*) AS total_count 
FROM activity_logs 
GROUP BY action_type 
ORDER BY total_count DESC;
```

### Option B: Quick Python One-Liner
```powershell
python -c "from app import app, db, ActivityLog; ctx=app.app_context(); ctx.push(); print([(a.id, a.action_type, a.description, a.ip_address) for a in ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(5).all()])"
```

---

## 🛡️ User Activity Logging Endpoints
- **Citizen Activity Timeline**: `GET /my-activity` (Jinja2) or `GET /api/user/activity` (JWT JSON API)
- **Admin Activity Monitor**: `GET /admin/activity-monitor` (Jinja2) or `GET /api/admin/activities` (JWT JSON API)
- **Public Complaint Tracker**: `GET /api/track/<ref_number>`
