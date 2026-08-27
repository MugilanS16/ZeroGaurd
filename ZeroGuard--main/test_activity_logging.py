"""
Automated Test Suite for ZeroGuard AI User Activity Logging & Login Auditing
Validates database logging for all user actions without breaking any existing endpoints.
"""

import sys
import os
import json

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from database.models import User, Complaint, ActivityLog, LoginHistory


def run_tests():
    print("=" * 70)
    print("[TEST SUITE] ZeroGuard AI - Activity & Login Logging Test Suite")
    print("=" * 70)

    client = app.test_client()

    with app.app_context():
        # Clear activity and login logs for a clean test run
        db.create_all()
        ActivityLog.query.delete()
        LoginHistory.query.delete()
        db.session.commit()

    passed = 0
    total = 11

    # -------------------------------------------------------------
    # 1. Test Registration Logging
    # -------------------------------------------------------------
    print("\n[Test 1/11] User Registration & Logging...")
    test_email = "test.logger@cybercrime.gov.in"
    with app.app_context():
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            Complaint.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()

    res = client.post("/api/auth/register", json={
        "fullname": "Test Logger User",
        "email": test_email,
        "phone": "+91 99999 88888",
        "password": "SecurePassword123!"
    })
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    data = res.get_json()
    user_id = data["user"]["id"]
    citizen_token = data["access_token"]

    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=user_id, action_type="register").first()
        assert act is not None, "Registration activity log entry missing!"
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
        log_h = LoginHistory.query.filter_by(user_id=user_id, success=True).first()
        assert log_h is not None, "LoginHistory registration entry missing!"
        print(f"  [OK] LoginHistory recorded: method={log_h.login_method}, success={log_h.success}")
    passed += 1

    # -------------------------------------------------------------
    # 2. Test Successful Login
    # -------------------------------------------------------------
    print("\n[Test 2/11] Successful Login Logging...")
    res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert res.status_code == 200
    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=user_id, action_type="login").order_by(ActivityLog.timestamp.desc()).first()
        assert act is not None, "Login activity log entry missing!"
        print(f"  [OK] ActivityLog recorded: {act.action_type} from IP {act.ip_address}")
        log_h = LoginHistory.query.filter_by(user_id=user_id, success=True).order_by(LoginHistory.timestamp.desc()).first()
        assert log_h is not None, "LoginHistory success entry missing!"
        print(f"  [OK] LoginHistory recorded: method={log_h.login_method}, success={log_h.success}")
    passed += 1

    # -------------------------------------------------------------
    # 3. Test Failed Login & Suspicious Pattern Simulation
    # -------------------------------------------------------------
    print("\n[Test 3/11] Failed Login & Anomaly Logging...")
    for i in range(3):
        res = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "WrongPassword999!"
        }, environ_overrides={'REMOTE_ADDR': '198.51.100.42'})
        assert res.status_code == 401

    with app.app_context():
        failed_acts = ActivityLog.query.filter_by(action_type="login_failed", ip_address="198.51.100.42").all()
        assert len(failed_acts) == 3, f"Expected 3 failed activity logs, found {len(failed_acts)}"
        failed_logins = LoginHistory.query.filter_by(success=False, ip_address="198.51.100.42").all()
        assert len(failed_logins) == 3, f"Expected 3 failed login history entries, found {len(failed_logins)}"
        print(f"  [OK] Recorded 3 failed login attempts from IP 198.51.100.42 for anomaly detection")
    passed += 1

    # -------------------------------------------------------------
    # 4. Test Report Submission Logging
    # -------------------------------------------------------------
    print("\n[Test 4/11] Report Submission Logging...")
    res = client.post("/api/reports",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "crime_type": "UPI Fraud",
            "description": "Lost 25,000 INR through a fraudulent Google Pay QR code scam request.",
            "entities": ["25,000 INR", "Google Pay", "Fraudulent QR"],
            "recommended_action": "Freeze bank account and dial 1930."
        }
    )
    assert res.status_code == 201
    report_data = res.get_json()["report"]
    ref_num = report_data["reference_number"]
    report_id = report_data["id"]

    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=user_id, action_type="report_submitted").first()
        assert act is not None, "Report submission log entry missing!"
        assert ref_num in act.description, f"Reference number {ref_num} not in log description!"
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
    passed += 1

    # -------------------------------------------------------------
    # 5. Test Live AI Classification Logging
    # -------------------------------------------------------------
    print("\n[Test 5/11] Live AI Analysis Logging...")
    res = client.post("/api/ai-crime/analyze",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"text": "Someone hacked my Instagram account and is demanding cryptocurrency ransom."}
    )
    assert res.status_code == 200
    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=user_id, action_type="ai_classify_used").first()
        assert act is not None, "AI classification activity log entry missing!"
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
    passed += 1

    # -------------------------------------------------------------
    # 6. Test AI Polish Enhancement Logging
    # -------------------------------------------------------------
    print("\n[Test 6/11] AI Polish Enhancement Logging...")
    res = client.post("/api/ai-enhance-report",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"text": "i got call from fake bank manager asking otp and money gone from sbi"}
    )
    assert res.status_code == 200
    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=user_id, action_type="ai_enhance_used").first()
        assert act is not None, "AI enhance activity log entry missing!"
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
    passed += 1

    # -------------------------------------------------------------
    # 7. Test AI Chatbot Usage Logging
    # -------------------------------------------------------------
    print("\n[Test 7/11] Floating AI Chatbot Usage Logging...")
    res = client.post("/api/ai-crime/chat",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"message": "What is the toll-free number for reporting credit card fraud?"}
    )
    assert res.status_code == 200
    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=user_id, action_type="chatbot_used").first()
        assert act is not None, "Chatbot activity log entry missing!"
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
    passed += 1

    # -------------------------------------------------------------
    # 8. Test Public Complaint Tracking Logging
    # -------------------------------------------------------------
    print("\n[Test 8/11] Public Complaint Tracker Logging...")
    res = client.get(f"/api/track/{ref_num}")
    assert res.status_code == 200
    with app.app_context():
        act = ActivityLog.query.filter_by(action_type="complaint_tracked").first()
        assert act is not None, "Complaint tracked activity log missing!"
        assert ref_num in act.description
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
    passed += 1

    # -------------------------------------------------------------
    # 9. Test Admin Status Update Logging
    # -------------------------------------------------------------
    print("\n[Test 9/11] Admin Status Update Logging...")
    res = client.post("/api/auth/login", json={
        "email": "admin@cybercrime.gov.in",
        "password": "AdminPass123!"
    })
    admin_token = res.get_json()["access_token"]
    admin_id = res.get_json()["user"]["id"]

    res = client.patch(f"/api/admin/reports/{report_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "In Review"}
    )
    assert res.status_code == 200
    with app.app_context():
        act = ActivityLog.query.filter_by(user_id=admin_id, action_type="status_updated").first()
        assert act is not None, "Status update activity log entry missing!"
        assert f"{ref_num} -> In Review" in act.description
        print(f"  [OK] ActivityLog recorded: {act.action_type} - {act.description}")
    passed += 1

    # -------------------------------------------------------------
    # 10. Test User Activity API & Jinja2 Template View
    # -------------------------------------------------------------
    print("\n[Test 10/11] User Activity API & My Activity Page...")
    res = client.get("/api/user/activity", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res.status_code == 200
    act_data = res.get_json()
    assert len(act_data["activities"]) > 0
    assert len(act_data["login_history"]) > 0
    print(f"  [OK] API returned {len(act_data['activities'])} user activities & {len(act_data['login_history'])} logins")

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Test Logger User"
        sess["user_email"] = test_email
    res = client.get("/my-activity")
    assert res.status_code == 200
    assert b"Privacy &amp; Security Note" in res.data or b"Privacy & Security Note" in res.data
    print("  [OK] /my-activity Jinja2 template rendered successfully with privacy notice")
    passed += 1

    # -------------------------------------------------------------
    # 11. Test Admin Activity Monitor API & Suspicious Pattern Detection
    # -------------------------------------------------------------
    print("\n[Test 11/11] Admin Activity Monitor & Suspicious IP Detection...")
    res = client.get("/api/admin/activities", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    admin_data = res.get_json()
    assert len(admin_data["activities"]) > 0
    assert any(s["ip"] == "198.51.100.42" and s["failed_count"] >= 3 for s in admin_data["suspicious_ips"])
    print(f"  [OK] Admin API detected suspicious IP: {admin_data['suspicious_ips']}")

    with client.session_transaction() as sess:
        sess["user_id"] = admin_id
        sess["user_name"] = "Admin User"
        sess["user_email"] = "admin@cybercrime.gov.in"
    res = client.get("/admin/activity-monitor")
    assert res.status_code == 200
    assert b"System Activity Monitor" in res.data
    assert b"198.51.100.42" in res.data
    print("  [OK] /admin/activity-monitor rendered successfully with flagged threat banner")
    passed += 1

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"[SUCCESS] ALL TESTS PASSED: {passed}/{total} features verified successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
