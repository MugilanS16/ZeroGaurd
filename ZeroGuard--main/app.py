"""
CrimeShield AI — Flask Backend
Decoupled REST API (JSON only) consumed by the React SPA on port 5173.
Legacy Jinja2 routes are kept intact; new /api/* routes return pure JSON.
Includes User Activity Logging & Login Auditing system.
"""

from flask import (
    Flask, render_template, request, redirect, session,
    send_file, flash, url_for, jsonify, send_from_directory
)
from flask_cors import CORS
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import uuid
import random
from datetime import datetime, timezone, timedelta
from functools import wraps

from config import Config
from extensions import db, jwt, migrate
from database.models import User, Complaint, ActivityLog, LoginHistory
from utils.activity_logger import log_activity, log_login
from ai.classifier import classify_crime
from ai.questions import get_questions, generate_dynamic_questions
from ai.guidance import get_guidance
from utils.upload import allowed_file, get_safe_filename
from pdf.report_generator import generate_complaint_pdf

app = Flask(__name__)
app.config.from_object(Config)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Vite dev server AND the production built files
CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
    }
})

# ─── EXTENSIONS ───────────────────────────────────────────────────────────────
db.init_app(app)
jwt.init_app(app)
migrate.init_app(app, db)



# ─────────────────────────────────────────────────────────────
#  SEED / INIT
# ─────────────────────────────────────────────────────────────

def seed_demo_users():
    """Ensure demo, Google SSO, DigiLocker, and admin users exist in database."""
    try:
        demo_accounts = [
            ("citizen@cybercrime.gov.in",      "Demo Citizen",             "+91 98765 43210",  "CitizenPass123!",    "citizen"),
            ("google.user@cybercrime.gov.in",   "Google SSO User",          "+91 98765 00001",  "GoogleSSOPass123!",  "citizen"),
            ("digilocker.user@cybercrime.gov.in","DigiLocker Verified User", "+91 98765 00002",  "DigiLockerPass123!", "citizen"),
            ("admin@cybercrime.gov.in",          "Admin User",               "+91 98765 99999",  "AdminPass123!",      "admin"),
        ]
        for email, name, phone, pwd, role in demo_accounts:
            if not User.query.filter_by(email=email).first():
                u = User(
                    fullname=name,
                    email=email,
                    phone=phone,
                    password=generate_password_hash(pwd),
                    role=role
                )
                db.session.add(u)
        db.session.commit()
    except Exception as e:
        print(f"[Seed] Error seeding demo users: {e}")


with app.app_context():
    db.create_all()
    seed_demo_users()


# ─────────────────────────────────────────────────────────────
#  HELPERS / DECORATORS
# ─────────────────────────────────────────────────────────────

def login_required(f):
    """Legacy session-based login check (for Jinja2 routes)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def jwt_admin_required(f):
    """JWT + admin role check for API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({"message": "Missing or invalid token"}), 401
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user or user.role != "admin":
            return jsonify({"message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


def generate_reference_number():
    """Generate a guaranteed unique CC-YYYY-NNNNN reference number."""
    year = datetime.now(timezone.utc).year
    max_id = db.session.query(db.func.max(Complaint.id)).scalar() or 0
    next_num = max_id + 1
    ref = f"CC-{year}-{next_num:05d}"
    while Complaint.query.filter_by(reference_number=ref).first() is not None:
        next_num += 1
        ref = f"CC-{year}-{next_num:05d}"
    return ref


def delete_session_uploads(filepaths: list):
    """Permanently delete temporary evidence files from the server."""
    for fp in filepaths:
        try:
            if fp and os.path.isfile(fp):
                os.remove(fp)
        except Exception as e:
            print(f"[Cleanup] Could not delete {fp}: {e}")


SEVERITY_MAP = {
    "UPI Fraud":                 "critical",
    "Banking Fraud":             "critical",
    "Credit/Debit Card Fraud":   "high",
    "Sextortion":                "critical",
    "Identity Theft":            "high",
    "Phishing":                  "high",
    "Social Media Hacking":      "medium",
    "Email Hacking":             "medium",
    "Malware/Ransomware":        "high",
    "Fake Customer Care Scam":   "high",
    "Investment Scam":           "high",
    "Job Scam":                  "medium",
    "Online Shopping Fraud":     "medium",
    "Lottery/Prize Scam":        "low",
    "Cyber Bullying":            "medium",
}

RISK_SCORES = {
    "UPI Fraud": 95, "Banking Fraud": 92, "Credit/Debit Card Fraud": 90,
    "Sextortion": 88, "Identity Theft": 85, "Malware/Ransomware": 85,
    "Investment Scam": 80, "Fake Customer Care Scam": 82,
    "Phishing": 75, "Social Media Hacking": 78,
    "Email Hacking": 72, "Job Scam": 70,
    "Online Shopping Fraud": 68, "Cyber Bullying": 65,
    "Lottery/Prize Scam": 60,
}


# ─────────────────────────────────────────────────────────────
#  STATIC / REACT SPA SERVING
# ─────────────────────────────────────────────────────────────

@app.route("/")
def serve_react_app():
    return send_from_directory(os.path.join(app.root_path, "frontend", "dist"), "index.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(app.root_path, "frontend", "dist", "assets"), filename)

@app.route("/api/home")
def home_api():
    return jsonify({"status": "success", "message": "CrimeShield AI API is running"})


# ─────────────────────────────────────────────────────────────
#  JWT AUTH API  (for React SPA)
# ─────────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    fullname = data.get("fullname", "").strip()
    email    = data.get("email", "").strip().lower()
    phone    = data.get("phone", "").strip()
    password = data.get("password", "")

    if not fullname or not email or not password:
        return jsonify({"message": "Name, email, and password are required."}), 400

    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "An account with this email already exists."}), 409

    user = User(
        fullname=fullname,
        email=email,
        phone=phone,
        password=generate_password_hash(password),
        role="citizen"
    )
    db.session.add(user)
    db.session.commit()

    log_activity(user.id, "register", f"Account registered for {user.email}")
    log_login(user.id, method="password", success=True)

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data     = request.get_json(silent=True) or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if email == "citizen@cybercrime.gov.in":
        seed_demo_users()

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        matched_id = user.id if user else None
        log_activity(matched_id, "login_failed", f"Failed login attempt for {email}" if email else "Failed login attempt")
        log_login(user_id=matched_id, method="password", success=False)
        return jsonify({"message": "Invalid email or password."}), 401

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    log_activity(user.id, "login", f"Successful login for {user.email}")
    log_login(user.id, method="password", success=True)

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 200


@app.route("/api/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def api_auth_refresh():
    user_id = str(get_jwt_identity())
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token}), 200


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def api_auth_me():
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass
    if not user_id:
        user_id = session.get("user_id")

    log_activity(user_id, "logout", "User logged out")
    session.clear()
    return jsonify({"message": "Logged out"}), 200


# ─────────────────────────────────────────────────────────────
#  REPORTS API
# ─────────────────────────────────────────────────────────────

@app.route("/api/reports", methods=["POST"])
@jwt_required()
def api_submit_report():
    user_id = int(get_jwt_identity())
    data    = request.get_json(silent=True) or {}

    description = data.get("description", "").strip()
    if len(description) < 20:
        return jsonify({"message": "Please describe the incident in at least 20 characters."}), 400

    crime_type         = data.get("crime_type", "Unknown")
    severity           = data.get("severity", SEVERITY_MAP.get(crime_type, "medium"))
    entities           = data.get("entities", [])
    recommended_action = data.get("recommended_action", "")

    reference_number = generate_reference_number()

    complaint = Complaint(
        user_id          = user_id,
        reference_number = reference_number,
        crime_type       = crime_type,
        severity         = severity,
        description      = description,
        entities         = json.dumps(entities),
        recommended_action = recommended_action,
        answers          = json.dumps(data.get("answers", [])),
        guidance_text    = json.dumps(data.get("guidance", [])),
        status           = "Pending",
    )
    db.session.add(complaint)
    db.session.commit()

    log_activity(user_id, "report_submitted", f"Report {reference_number} submitted ({crime_type})")

    return jsonify({
        "message": "Report submitted successfully.",
        "report": complaint.to_dict()
    }), 201


@app.route("/api/reports/mine", methods=["GET"])
@jwt_required()
def api_my_reports():
    user_id = int(get_jwt_identity())
    complaints = (
        Complaint.query
        .filter_by(user_id=user_id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return jsonify({"reports": [c.to_dict() for c in complaints]}), 200


@app.route("/api/reports/<int:report_id>", methods=["GET"])
@jwt_required()
def api_get_report(report_id):
    user_id   = int(get_jwt_identity())
    user      = db.session.get(User, user_id)
    complaint = db.session.get(Complaint, report_id)
    if not complaint:
        return jsonify({"message": "Report not found"}), 404

    if complaint.user_id != user_id and user.role != "admin":
        return jsonify({"message": "Forbidden"}), 403

    return jsonify({"report": complaint.to_dict()}), 200


# ─────────────────────────────────────────────────────────────
#  ADMIN API
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/reports", methods=["GET"])
@jwt_admin_required
def api_admin_reports():
    crime_type_filter = request.args.get("crime_type")
    severity_filter   = request.args.get("severity")
    status_filter     = request.args.get("status")

    query = Complaint.query
    if crime_type_filter:
        query = query.filter(Complaint.crime_type == crime_type_filter)
    if severity_filter:
        query = query.filter(Complaint.severity == severity_filter)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return jsonify({"reports": [c.to_dict() for c in complaints]}), 200


@app.route("/api/admin/reports/<int:report_id>", methods=["PATCH"])
@jwt_admin_required
def api_admin_update_report(report_id):
    data      = request.get_json(silent=True) or {}
    complaint = db.session.get(Complaint, report_id)
    if not complaint:
        return jsonify({"message": "Report not found"}), 404

    allowed_statuses = ["Pending", "In Review", "Resolved"]
    new_status = data.get("status")
    if new_status and new_status in allowed_statuses:
        complaint.status = new_status
        db.session.commit()
        admin_user_id = int(get_jwt_identity())
        log_activity(admin_user_id, "status_updated", f"{complaint.reference_number} -> {new_status}")

    return jsonify({"report": complaint.to_dict()}), 200


@app.route("/api/admin/stats", methods=["GET"])
@jwt_admin_required
def api_admin_stats():
    total     = Complaint.query.count()
    pending   = Complaint.query.filter_by(status="Pending").count()
    in_review = Complaint.query.filter_by(status="In Review").count()
    resolved  = Complaint.query.filter_by(status="Resolved").count()

    # Counts by severity
    severity_stats = {}
    for sev in ["low", "medium", "high", "critical"]:
        severity_stats[sev] = Complaint.query.filter_by(severity=sev).count()

    # Counts by crime_type (top 10)
    from sqlalchemy import func
    type_rows = (
        db.session.query(Complaint.crime_type, func.count(Complaint.id).label("count"))
        .group_by(Complaint.crime_type)
        .order_by(func.count(Complaint.id).desc())
        .limit(10)
        .all()
    )
    type_stats = [{"name": r.crime_type, "count": r.count} for r in type_rows]

    return jsonify({
        "total": total,
        "pending": pending,
        "in_review": in_review,
        "resolved": resolved,
        "by_severity": severity_stats,
        "by_type": type_stats,
    }), 200


# ─────────────────────────────────────────────────────────────
#  ACTIVITY LOG & AUDIT APIS (for React SPA)
# ─────────────────────────────────────────────────────────────

@app.route("/api/user/activity", methods=["GET"])
@jwt_required()
def api_user_activity():
    user_id = int(get_jwt_identity())
    activities = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(50).all()
    logins = LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.timestamp.desc()).limit(20).all()
    return jsonify({
        "activities": [a.to_dict() for a in activities],
        "login_history": [l.to_dict() for l in logins]
    }), 200


@app.route("/api/admin/activities", methods=["GET"])
@jwt_admin_required
def api_admin_activities():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action_type = request.args.get("action_type", "").strip()
    user_query = request.args.get("user_query", "").strip()

    query = ActivityLog.query
    if action_type:
        query = query.filter(ActivityLog.action_type == action_type)
    if user_query:
        query = query.join(User, isouter=True).filter(
            db.or_(User.email.ilike(f"%{user_query}%"), User.fullname.ilike(f"%{user_query}%"))
        )

    pagination = query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    from sqlalchemy import func
    suspicious_rows = (
        db.session.query(LoginHistory.ip_address, func.count(LoginHistory.id).label("failed_count"))
        .filter(LoginHistory.success == False, LoginHistory.timestamp >= cutoff)
        .group_by(LoginHistory.ip_address)
        .having(func.count(LoginHistory.id) >= 3)
        .all()
    )
    suspicious_ips = [{"ip": r[0], "failed_count": r[1]} for r in suspicious_rows]

    return jsonify({
        "activities": [a.to_dict() for a in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "suspicious_ips": suspicious_ips
    }), 200


# ─────────────────────────────────────────────────────────────
#  AI CRIME API  (JSON only)
# ─────────────────────────────────────────────────────────────

@app.route("/api/ai-crime/analyze", methods=["POST"])
def api_ai_analyze():
    """Real-time crime analysis — called as user types (debounced from frontend)."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if len(text) < 10:
        return jsonify({
            "crime_type": None,
            "severity": None,
            "risk_score": 0,
            "entities": [],
            "recommended_action": "",
            "method": None
        }), 200

    result     = classify_crime(text)
    crime_type = result.get("crime_type", "Unknown")
    severity   = SEVERITY_MAP.get(crime_type, "medium")
    risk_score = RISK_SCORES.get(crime_type, 65)
    guidance   = get_guidance(crime_type)
    recommended_action = guidance[0] if guidance else "Contact 1930 immediately."

    # Identify user if token present
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass
    if not user_id:
        user_id = session.get("user_id")

    log_activity(user_id, "ai_classify_used", f"Live analysis: {crime_type} ({severity})")

    return jsonify({
        "crime_type":         crime_type,
        "severity":           severity,
        "risk_score":         risk_score,
        "entities":           result.get("entities", []),
        "recommended_action": recommended_action,
        "method":             result.get("method", "keyword"),
        "guidance":           guidance,
    }), 200


@app.route("/api/ai-crime/chat", methods=["POST"])
def api_ai_chat():
    """
    Stateless chatbot endpoint — frontend sends full history each time.
    Returns a reply JSON with crime_type and risk info.
    """
    from ai.classifier import classify_crime, _call_gemini
    from ai.guidance import get_guidance

    data         = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    history      = data.get("history", [])  # [{role, text}, ...]
    crime_type   = data.get("crime_type")   # passed from frontend after first classify

    # Identify user if token present
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass
    if not user_id:
        user_id = session.get("user_id")

    log_activity(user_id, "chatbot_used", f"AI Widget: {crime_type or 'General Inquiry'}")

    if not user_message:
        return jsonify({"reply": "Please describe your incident.", "crime_type": None, "risk": 0}), 200

    # First message: classify
    if not crime_type:
        result     = classify_crime(user_message)
        crime_type = result["crime_type"]
        method     = result["method"]
        guidance   = get_guidance(crime_type)
        risk       = RISK_SCORES.get(crime_type, 65)

        steps_text = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(guidance))
        reply = (
            f"I identified this as **{crime_type}** "
            f"({'AI' if method == 'ai' else 'Rule-based'} classification).\n\n"
            f"**Immediate steps:**\n{steps_text}\n\n"
            f"Feel free to ask about any step, evidence to preserve, or how to file a formal complaint."
        )

        return jsonify({
            "reply":                reply,
            "crime_type":           crime_type,
            "risk":                 risk,
            "guidance":             guidance,
            "is_new_classification": True
        }), 200

    # Follow-up: use Gemini with context
    guidance = get_guidance(crime_type)
    reset_triggers = ["new incident", "different problem", "another issue",
                      "start over", "reset", "new complaint"]
    if any(t in user_message.lower() for t in reset_triggers):
        return jsonify({
            "reply":      "Sure! Describe your new incident and I'll classify it.",
            "crime_type": None, "risk": 0
        }), 200

    guidance_text = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(guidance))
    hist_text     = "\n\n".join(f"{m['role'].upper()}: {m['text']}" for m in history[-8:])
    system_prompt = (
        f"You are a cybercrime victim support assistant for India.\n"
        f"The user has reported a **{crime_type}** incident.\n\n"
        f"Recommended steps:\n{guidance_text}\n\n"
        f"Key resources:\n"
        f"- National Cybercrime Helpline: 1930 (24x7)\n"
        f"- Online portal: cybercrime.gov.in\n"
        f"- RBI Banking helpline: 14440\n\n"
        f"RULES: Be specific, empathetic, and concise. Answer in plain markdown text."
    )
    full_prompt = f"{system_prompt}\n\nConversation:\n{hist_text}\nUSER: {user_message}\n\nASSISTANT:"

    try:
        reply = _call_gemini(full_prompt)
    except Exception:
        steps_html = "\n".join(f"- {s}" for s in guidance)
        reply = f"For your **{crime_type}** case:\n\n{steps_html}\n\nCall **1930** for immediate assistance."

    return jsonify({
        "reply":      reply,
        "crime_type": crime_type,
        "risk":       RISK_SCORES.get(crime_type, 65),
    }), 200


# ─────────────────────────────────────────────────────────────
#  PUBLIC COMPLAINT TRACKER
# ─────────────────────────────────────────────────────────────

@app.route("/api/track/<string:ref_number>", methods=["GET"])
def api_track_complaint(ref_number):
    complaint = Complaint.query.filter_by(reference_number=ref_number.strip()).first()
    log_activity(None, "complaint_tracked", f"Tracked reference {ref_number}")
    if not complaint:
        return jsonify({"message": "Complaint not found", "found": False}), 404
    return jsonify({
        "found": True,
        "reference_number": complaint.reference_number,
        "crime_type": complaint.crime_type,
        "status": complaint.status,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None
    }), 200


# ─────────────────────────────────────────────────────────────
#  LEGACY SESSION-BASED ROUTES (kept intact for backward compat)
# ─────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    """Legacy session login (for existing Jinja2 flows)."""
    if "user_id" in session:
        return jsonify({"status": "success", "message": "Already logged in"}), 200

    data     = request.get_json(silent=True) or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if email == "citizen@cybercrime.gov.in":
        seed_demo_users()

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session["user_id"]    = user.id
        session["user_name"]  = user.fullname
        session["user_email"] = user.email
        session["user_phone"] = user.phone or ""
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        log_activity(user.id, "login", f"Successful legacy login for {user.email}")
        log_login(user.id, method="password", success=True)
        return jsonify({"status": "success", "user": {"name": user.fullname}}), 200

    matched_id = user.id if user else None
    log_activity(matched_id, "login_failed", f"Failed legacy login for {email}" if email else "Failed login")
    log_login(user_id=matched_id, method="password", success=False)
    return jsonify({"status": "error", "message": "Invalid email or password."}), 401


@app.route("/auth/google")
def auth_google():
    email = request.args.get("email", "google.user@cybercrime.gov.in").strip().lower()
    name  = request.args.get("name", "Google SSO User").strip()
    user  = User.query.filter_by(email=email).first()
    if not user:
        user = User(fullname=name, email=email, phone="+91 98765 00001",
                    password=generate_password_hash("GoogleSSOPass123!"))
        db.session.add(user)
        db.session.commit()
    session["user_id"]    = user.id
    session["user_name"]  = user.fullname
    session["user_email"] = user.email
    session["user_phone"] = user.phone or ""
    log_activity(user.id, "login", "Google SSO login")
    log_login(user.id, method="google_sso", success=True)
    return redirect(url_for("dashboard"))


@app.route("/auth/digilocker")
def auth_digilocker():
    email = request.args.get("email", "digilocker.user@cybercrime.gov.in").strip().lower()
    name  = request.args.get("name", "DigiLocker Verified User").strip()
    user  = User.query.filter_by(email=email).first()
    if not user:
        user = User(fullname=name, email=email, phone="+91 98765 00002",
                    password=generate_password_hash("DigiLockerPass123!"))
        db.session.add(user)
        db.session.commit()
    session["user_id"]    = user.id
    session["user_name"]  = user.fullname
    session["user_email"] = user.email
    session["user_phone"] = user.phone or ""
    log_activity(user.id, "login", "DigiLocker login")
    log_login(user.id, method="digilocker", success=True)
    return redirect(url_for("dashboard"))


@app.route("/api/logout", methods=["POST"])
def logout():
    user_id = session.get("user_id")
    log_activity(user_id, "logout", "User logged out")
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"}), 200


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email    = request.form.get("email", "").strip().lower()
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not fullname or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="Email already registered.")

        user = User(fullname=fullname, email=email, phone=phone,
                    password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        log_activity(user.id, "register", f"Registered account for {email}")
        log_login(user.id, method="password", success=True)
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user_id    = session["user_id"]
    complaints = (Complaint.query.filter_by(user_id=user_id)
                  .order_by(Complaint.created_at.desc()).all())
    total     = len(complaints)
    pending   = sum(1 for c in complaints if c.status == "Pending")
    resolved  = sum(1 for c in complaints if c.status == "Resolved")
    in_review = sum(1 for c in complaints if c.status == "In Review")
    return render_template("dashboard.html",
        username=session["user_name"], complaints=complaints,
        total=total, pending=pending, resolved=resolved, in_review=in_review)


@app.route("/my-activity")
@login_required
def my_activity_view():
    user_id = session["user_id"]
    activities = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(50).all()
    logins = LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.timestamp.desc()).limit(20).all()
    return render_template("my_activity.html",
                           username=session.get("user_name", "User"),
                           user_email=session.get("user_email", ""),
                           activities=activities,
                           logins=logins)


@app.route("/admin/activity-monitor")
def admin_activity_monitor_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user or user.role != "admin":
        flash("Admin login required.", "danger")
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)
    action_type = request.args.get("action_type", "").strip()
    user_query = request.args.get("user_query", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = ActivityLog.query
    if action_type:
        query = query.filter(ActivityLog.action_type == action_type)
    if user_query:
        query = query.join(User, isouter=True).filter(
            db.or_(User.email.ilike(f"%{user_query}%"), User.fullname.ilike(f"%{user_query}%"))
        )
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            query = query.filter(ActivityLog.timestamp >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(ActivityLog.timestamp <= dt)
        except Exception:
            pass

    pagination = query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=50, error_out=False)

    # Detect suspicious IPs (>= 3 failed logins in last 24 hours)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    from sqlalchemy import func
    suspicious_rows = (
        db.session.query(LoginHistory.ip_address, func.count(LoginHistory.id).label("failed_count"))
        .filter(LoginHistory.success == False, LoginHistory.timestamp >= cutoff)
        .group_by(LoginHistory.ip_address)
        .having(func.count(LoginHistory.id) >= 3)
        .all()
    )
    suspicious_ips = {r[0]: r[1] for r in suspicious_rows}

    return render_template("admin/activity_monitor.html",
                           pagination=pagination,
                           activities=pagination.items,
                           suspicious_ips=suspicious_ips,
                           action_type=action_type,
                           user_query=user_query,
                           date_from=date_from,
                           date_to=date_to,
                           username=user.fullname)


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        description = request.form.get("description", "").strip()
        if len(description) < 20:
            return render_template("report.html", error="Please describe the incident in at least 20 characters.")
        result     = classify_crime(description)
        crime_type = result["crime_type"]
        method     = result["method"]
        redacted   = result["redacted_text"]
        session["report"] = {
            "description": description,
            "redacted_description": redacted,
            "crime_type": crime_type,
            "classification_method": method,
            "answers": [], "guidance": [],
            "evidence_paths": [], "evidence_filenames": [],
        }
        log_activity(session.get("user_id"), "report_started", f"Incident draft: {crime_type}")
        return redirect(url_for("questions_page"))
    return render_template("report.html")


@app.route("/questions-page")
@login_required
def questions_page():
    report_data = session.get("report")
    if not report_data:
        return redirect(url_for("report"))
    crime_type  = report_data["crime_type"]
    description = report_data.get("description", "")
    questions   = generate_dynamic_questions(crime_type, description)
    report_data["generated_questions"] = questions
    session["report"] = report_data
    session.modified = True
    return render_template("questions.html", crime_type=crime_type, questions=questions,
                           classification_method=report_data.get("classification_method", "keyword"))


@app.route("/submit-answers", methods=["POST"])
@login_required
def submit_answers():
    report_data = session.get("report")
    if not report_data:
        return redirect(url_for("report"))
    crime_type = report_data["crime_type"]
    questions  = report_data.get("generated_questions", get_questions(crime_type))
    answers    = []
    for i, q in enumerate(questions):
        answers.append({"question": q, "answer": request.form.get(f"answer_{i}", "").strip()})
    guidance             = get_guidance(crime_type)
    report_data["answers"]  = answers
    report_data["guidance"] = guidance
    session["report"]       = report_data
    session.modified = True
    return redirect(url_for("guidance_page"))


@app.route("/guidance-page")
@login_required
def guidance_page():
    report_data = session.get("report")
    if not report_data:
        return redirect(url_for("report"))
    return render_template("guidance.html", crime_type=report_data["crime_type"],
                           guidance=report_data["guidance"], answers=report_data["answers"])


@app.route("/submit-evidence", methods=["POST"])
@login_required
def submit_evidence():
    report_data = session.get("report")
    if not report_data:
        return redirect(url_for("report"))
    uploaded_files  = request.files.getlist("evidence")
    evidence_paths  = []
    evidence_filenames = []
    for file in uploaded_files:
        if file and file.filename and file.filename != "":
            if allowed_file(file.filename):
                safe_name = get_safe_filename(file.filename)
                filepath  = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
                file.save(filepath)
                evidence_paths.append(filepath)
                evidence_filenames.append(file.filename)
    report_data["evidence_paths"]     = evidence_paths
    report_data["evidence_filenames"] = evidence_filenames
    session["report"] = report_data
    session.modified  = True
    log_activity(session.get("user_id"), "evidence_uploaded", f"{len(evidence_filenames)} files uploaded")
    return redirect(url_for("preview"))


@app.route("/preview")
@login_required
def preview():
    report_data = session.get("report")
    if not report_data:
        return redirect(url_for("report"))
    return render_template("preview.html",
        username=session["user_name"], user_email=session.get("user_email", ""),
        user_phone=session.get("user_phone", ""),
        crime_type=report_data["crime_type"], description=report_data["description"],
        answers=report_data["answers"], guidance=report_data["guidance"],
        evidence_filenames=report_data["evidence_filenames"],
        classification_method=report_data.get("classification_method", "keyword"))


@app.route("/generate-pdf", methods=["POST"])
@login_required
def generate_pdf():
    report_data = session.get("report")
    if not report_data:
        return redirect(url_for("report"))
    user_id    = session["user_id"]
    user_name  = session["user_name"]
    user_email = session.get("user_email", "")
    user_phone = session.get("user_phone", "")
    crime_type        = report_data.get("crime_type", "Cyber Crime")
    description       = report_data.get("description", "")
    answers           = report_data.get("answers", [])
    guidance          = report_data.get("guidance", [])
    evidence_paths    = report_data.get("evidence_paths", [])
    evidence_filenames = report_data.get("evidence_filenames", [])
    date_filed        = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    reference_number  = generate_reference_number()

    pdf_buffer = generate_complaint_pdf(
        complaint_id=reference_number, user_name=user_name, user_email=user_email,
        user_phone=user_phone, crime_type=crime_type, description=description,
        answers=answers, guidance=guidance, evidence_files=evidence_filenames,
        evidence_paths=evidence_paths, date_filed=date_filed
    )
    complaint = Complaint(
        user_id=user_id, reference_number=reference_number, crime_type=crime_type,
        severity=SEVERITY_MAP.get(crime_type, "medium"), description=description,
        answers=json.dumps(answers), guidance_text=json.dumps(guidance),
        evidence_filenames=",".join(evidence_filenames), status="Pending"
    )
    db.session.add(complaint)
    db.session.commit()
    log_activity(user_id, "report_submitted", f"Report {reference_number} generated ({crime_type})")
    delete_session_uploads(evidence_paths)
    session.pop("report", None)
    return send_file(pdf_buffer, as_attachment=True,
                     download_name=f"cybercrime_complaint_{reference_number}.pdf",
                     mimetype="application/pdf")


@app.route("/chatbot")
def chatbot():
    session.pop("chat_context", None)
    return render_template("chatbot.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    Legacy session-based Gemini chat (for Jinja2 chatbot page).
    Kept intact; the React widget uses /api/ai-crime/chat instead.
    """
    from ai.classifier import classify_crime, _call_gemini
    from ai.guidance import get_guidance

    data         = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    user_id = session.get("user_id")

    if not user_message:
        return {"reply": "Please describe your incident.", "crime_type": None, "risk": 0}

    ctx = session.get("chat_context", {"crime_type": None, "guidance": [], "history": []})
    is_first = ctx["crime_type"] is None

    if is_first:
        result     = classify_crime(user_message)
        crime_type = result["crime_type"]
        method     = result["method"]
        guidance   = get_guidance(crime_type)
        ctx["crime_type"] = crime_type
        ctx["guidance"]   = guidance
        ctx["history"]    = []
        risk       = RISK_SCORES.get(crime_type, 65)
        steps_html = "<br>".join(f"<strong>Step {i+1}:</strong> {s}" for i, s in enumerate(guidance))
        reply      = (
            f"I identified this as <strong>{crime_type}</strong> "
            f"<em style='font-size:0.8em;color:#888;'>({'🤖 AI' if method == 'ai' else '⚡ Rule-Based'})</em>.<br><br>"
            f"<strong>Immediate steps:</strong><br>{steps_html}<br><br>"
            f"<em style='color:#888;font-size:0.82em;'>Ask me anything about this case.</em>"
        )
        ctx["history"] += [{"role": "user", "text": user_message}, {"role": "assistant", "text": reply}]
        session["chat_context"] = ctx
        log_activity(user_id, "chatbot_used", f"Legacy Chat: {crime_type}")
        return {"reply": reply, "crime_type": crime_type, "risk": risk, "is_new_classification": True}

    crime_type = ctx["crime_type"]
    guidance   = ctx["guidance"]
    history    = ctx.get("history", [])

    reset_triggers = ["new incident", "different problem", "another issue", "start over", "reset"]
    if any(t in user_message.lower() for t in reset_triggers):
        session.pop("chat_context", None)
        return {"reply": "Sure! Describe your new incident.", "crime_type": None, "risk": 0}

    guidance_numbered = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(guidance))
    system_prompt = (
        f"You are a cybercrime victim support assistant for India.\n"
        f"The user has reported a {crime_type} incident.\n\n"
        f"Recommended steps:\n{guidance_numbered}\n\n"
        f"Key resources:\n- 1930 (24x7)\n- cybercrime.gov.in\n- RBI: 14440\n\n"
        f"RULES: Be specific, empathetic. Format using HTML <strong> and <br>. No markdown."
    )
    conv_turns = "\n\n".join(f"{m['role'].upper()}: {m['text']}" for m in history[-8:])
    full_prompt = f"{system_prompt}\n\nConversation:\n{conv_turns}\nUSER: {user_message}\n\nASSISTANT:"

    gemini_reply = None
    try:
        gemini_reply = _call_gemini(full_prompt)
        gemini_reply = (gemini_reply
            .replace("**", "").replace("##", "").replace("# ", "")
            .replace("\n\n", "<br><br>").replace("\n", "<br>"))
    except Exception as e:
        print(f"[Chat] Gemini unavailable: {e}")
        steps_html   = "<br>".join(f"<strong>Step {i+1}:</strong> {s}" for i, s in enumerate(guidance))
        gemini_reply = f"For your <strong>{crime_type}</strong> case:<br><br>{steps_html}<br><br>Call <strong>1930</strong> for immediate assistance."

    ctx["history"] += [{"role": "user", "text": user_message}, {"role": "assistant", "text": gemini_reply}]
    if len(ctx["history"]) > 20:
        ctx["history"] = ctx["history"][-20:]
    session["chat_context"] = ctx

    log_activity(user_id, "chatbot_used", f"Legacy Chat: {crime_type}")
    return {"reply": gemini_reply, "crime_type": crime_type, "risk": None, "is_new_classification": False}


@app.route("/awareness")
def awareness():
    return render_template("awareness.html")

@app.route("/emergency")
def emergency():
    return render_template("emergency.html")


@app.route("/api/ai-enhance-report", methods=["POST"])
def api_enhance_report():
    from ai.classifier import _call_gemini
    from ai.redact import redact_sensitive_data
    data     = request.get_json(silent=True) or {}
    raw_text = data.get("text", "").strip()
    if len(raw_text) < 15:
        return jsonify({"error": "Please type at least 15 characters before using AI Polish."}), 400

    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass
    if not user_id:
        user_id = session.get("user_id")

    log_activity(user_id, "ai_enhance_used", "AI Polish executed")

    redacted_text = redact_sensitive_data(raw_text)
    prompt = f"""You are a legal cybercrime reporting assistant for the National Cyber Crime Reporting Portal of India.
Take the following victim's incident description and rewrite it into a clear, professional, structured formal complaint draft in English.

Input text:
"{redacted_text}"

Rules:
1. Translate to English if written in a regional language.
2. Preserve all factual details.
3. Structure: Incident Summary, Modus Operandi, Loss & Relief Requested.
4. Do NOT add fabricated facts. Keep language objective and formal.
5. Output ONLY the polished report text without markdown symbols.
"""
    try:
        enhanced = _call_gemini(prompt)
        enhanced = enhanced.replace("**", "").replace("### ", "").replace("## ", "").replace("# ", "").strip()
        return jsonify({"enhanced_text": enhanced})
    except Exception as e:
        print(f"[AI Enhance] Fallback used: {e}")
        fallback = f"INCIDENT SUMMARY:\n{raw_text}\n\nKEY DETAILS:\n• Reported Date: {datetime.now().strftime('%d %B %Y')}\n• Status: Drafted for formal submission."
        return jsonify({"enhanced_text": fallback})


@app.route("/api/ai-quick-classify", methods=["POST"])
def api_quick_classify():
    from ai.classifier import classify_crime
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if len(text) < 15:
        return jsonify({"crime_type": None, "risk": "Normal"})

    res        = classify_crime(text)
    crime_type = res.get("crime_type", "Cyber Crime")
    severity   = SEVERITY_MAP.get(crime_type, "medium")

    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass
    if not user_id:
        user_id = session.get("user_id")

    log_activity(user_id, "ai_classify_used", f"Quick classify: {crime_type}")

    return jsonify({
        "crime_type": crime_type,
        "severity":   severity,
        "risk":       severity.upper(),
        "method":     res.get("method", "ai"),
        "entities":   res.get("entities", [])
    })


# ─────────────────────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)