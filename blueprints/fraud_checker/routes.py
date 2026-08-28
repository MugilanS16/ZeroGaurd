import os
from flask import render_template, request, jsonify, session
from datetime import datetime

from . import fraud_checker_bp
from ai.fraud_checker import detect_input_type, check_url, check_phone_number
from database import db
from database.models import ActivityLog

@fraud_checker_bp.route('/fraud-checker', methods=['GET'])
def index():
    """Renders the standalone Fraud URL & Number Checker public page."""
    return render_template('fraud_checker.html')

@fraud_checker_bp.route('/api/fraud-checker/check', methods=['POST'])
def check_fraud():
    """
    API endpoint for checking a URL or Phone Number against Google Safe Browsing,
    the platform complaint database, and rule-based heuristics.
    """
    data = request.get_json(silent=True) or request.form
    raw_input = (data.get('input') or data.get('query') or '').strip()

    if not raw_input:
        return jsonify({
            "status": "error",
            "message": "Please enter a valid URL (e.g. sbi-update-kyc.tk) or Indian Phone Number (e.g. +91 98765 43210)."
        }), 400

    input_type = detect_input_type(raw_input)

    if input_type == 'url':
        result = check_url(raw_input)
    elif input_type == 'phone':
        result = check_phone_number(raw_input)
    else:
        # If unknown format, provide helpful guidance
        return jsonify({
            "status": "error",
            "message": "Unrecognized format. Please provide a full website link (e.g., https://example.com) or a phone number (e.g., +91 9876543210)."
        }), 400

    # If the user is logged in, log the scan to ActivityLog
    user_id = session.get('user_id')
    if user_id:
        try:
            log_entry = ActivityLog(
                user_id=user_id,
                action='fraud_checker_scan',
                details=f"Checked {result.get('input_type')}: {raw_input} -> {result.get('risk_level')} Risk ({result.get('risk_score')}/100)",
                ip_address=request.remote_addr or '127.0.0.1',
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"[ACTIVITY LOG ERROR] {e}")

    return jsonify({
        "status": "success",
        "data": result
    })
