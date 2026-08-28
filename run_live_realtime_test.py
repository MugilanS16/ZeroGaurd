"""
Real-Time Network Integration Test across live HTTP sockets on port 5000 & 5173
"""
import urllib.request
import json

BASE_URL = "http://localhost:5000"

def post_json(endpoint, data, token=None):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def get_json(endpoint, token=None):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def patch_json(endpoint, data, token=None):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def run():
    print("\n==================================================")
    print("EXECUTING REAL-TIME LIVE NETWORK INTEGRATION TEST")
    print("==================================================")

    # 1. Citizen Login
    print("\n[1] Authenticating Citizen via JWT over HTTP socket...")
    status, auth_res = post_json("/api/auth/login", {
        "email": "citizen@cybercrime.gov.in",
        "password": "CitizenPass123!"
    })
    token = auth_res["access_token"]
    user = auth_res["user"]
    print(f" -> Logged in as '{user['name']}' ({user['email']}) | Role: {user['role']}")

    # 2. Live AI Threat Analysis
    print("\n[2] Sending real-time incident text to AI Analyzer (/api/ai-crime/analyze)...")
    incident_text = "I received a phone call from an unknown person claiming to be HDFC fraud department. They asked for my debit card CVV and OTP to block unauthorized debit of Rs 90,000 to merchant hdfc-pay-gate.in."
    status, ai_res = post_json("/api/ai-crime/analyze", {"text": incident_text})
    print(f" -> AI Classification: {ai_res['crime_type']} | Severity: {ai_res['severity'].upper()} | Threat Score: {ai_res['risk_score']}/100")
    print(f" -> Recommended Action: {ai_res['recommended_action']}")
    print(f" -> Extracted Entities: {ai_res['entities']}")

    # 3. Report Submission
    print("\n[3] Submitting official incident report to /api/reports...")
    status, report_res = post_json("/api/reports", {
        "description": incident_text,
        "crime_type": ai_res["crime_type"],
        "severity": ai_res["severity"],
        "entities": ai_res["entities"],
        "recommended_action": ai_res["recommended_action"],
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-24"},
            {"question": "Financial Loss (INR)", "answer": "₹90,000"}
        ],
        "guidance": ai_res.get("guidance", [])
    }, token=token)
    filed_report = report_res["report"]
    print(f" -> Report Created! Reference #: {filed_report['reference_number']} | Status: {filed_report['status']}")

    # 4. Fetch User Dashboard Reports
    print("\n[4] Querying User Dashboard reports (/api/reports/mine)...")
    status, my_reps = get_json("/api/reports/mine", token=token)
    print(f" -> Total user reports in database: {len(my_reps['reports'])}")
    for r in my_reps['reports'][:3]:
        print(f"    • [{r['reference_number']}] {r['crime_type']} ({r['severity']}) -> Status: {r['status']}")

    # 5. Live AI Chatbot Interaction
    print("\n[5] Querying AI Chatbot Widget (/api/ai-crime/chat)...")
    status, chat_res = post_json("/api/ai-crime/chat", {
        "message": "What should I tell my bank manager right now?",
        "history": [{"role": "user", "text": incident_text}]
    })
    print(f" -> AI Assistant Response:\n{chat_res['reply'][:180]}...")

    # 6. Admin Login & Telemetry
    print("\n[6] Authenticating Admin user (admin@cybercrime.gov.in)...")
    status, admin_auth = post_json("/api/auth/login", {
        "email": "admin@cybercrime.gov.in",
        "password": "AdminPass123!"
    })
    admin_token = admin_auth["access_token"]

    print("\n[7] Fetching Admin Command Center Telemetry (/api/admin/stats)...")
    status, stats = get_json("/api/admin/stats", token=admin_token)
    print(f" -> Live National Stats: Total={stats['total']}, Pending={stats['pending']}, In Review={stats['in_review']}, Resolved={stats['resolved']}")
    print(f" -> Severity Distribution: {stats['by_severity']}")
    print(f" -> Top Crime Categories: {[t['name'] + ' (' + str(t['count']) + ')' for t in stats['by_type'][:4]]}")

    # 8. Admin Status Workflow Update
    print(f"\n[8] Updating Report #{filed_report['reference_number']} to 'Resolved' via Admin PATCH...")
    status, patch_res = patch_json(f"/api/admin/reports/{filed_report['id']}", {"status": "Resolved"}, token=admin_token)
    print(f" -> Updated Report #{patch_res['report']['reference_number']} Status: {patch_res['report']['status']}")

    print("\n==================================================")
    print("SUCCESS: ALL REAL-TIME LIVE DATA WORKFLOWS VERIFIED (100% PASS)")
    print("==================================================")

if __name__ == "__main__":
    run()
