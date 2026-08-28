"""
Automated End-to-End API Test Suite for CrimeShield AI
"""
from app import app, db, seed_demo_users

def run_tests():
    client = app.test_client()

    print("=== TEST 1: API Health Check ===")
    res = client.get("/api/home")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("PASS: /api/home returned 200", res.get_json())

    print("\n=== TEST 2: Citizen Login & JWT Generation ===")
    res = client.post("/api/auth/login", json={
        "email": "citizen@cybercrime.gov.in",
        "password": "CitizenPass123!"
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code} {res.data}"
    citizen_data = res.get_json()
    citizen_token = citizen_data["access_token"]
    assert citizen_token, "No access token received"
    print("PASS: Citizen logged in. Token:", citizen_token[:25] + "...")

    print("\n=== TEST 3: Hydrate User (/api/auth/me) ===")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res.status_code == 200
    user_me = res.get_json()["user"]
    assert user_me["email"] == "citizen@cybercrime.gov.in"
    print("PASS: /api/auth/me verified for user:", user_me["name"])

    print("\n=== TEST 4: Live AI Crime Analysis (/api/ai-crime/analyze) ===")
    sample_text = "Someone called pretending to be SBI bank officer and asked for OTP to update KYC, then debited 50000 rupees via UPI to 9876543210@paytm."
    res = client.post("/api/ai-crime/analyze", json={"text": sample_text})
    assert res.status_code == 200
    ai_res = res.get_json()
    print("PASS: AI Analysis returned:", {
        "crime_type": ai_res.get("crime_type"),
        "severity": ai_res.get("severity"),
        "risk_score": ai_res.get("risk_score")
    })

    print("\n=== TEST 5: Submit Report (/api/reports) ===")
    res = client.post("/api/reports",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "description": sample_text,
            "crime_type": ai_res.get("crime_type", "UPI Fraud"),
            "severity": ai_res.get("severity", "critical"),
            "entities": ["SBI", "9876543210@paytm", "₹50,000"],
            "recommended_action": "Freeze bank account immediately and call 1930.",
            "answers": [{"question": "Incident Date", "answer": "2026-08-24"}],
            "guidance": ["Call 1930", "Block UPI handle", "Notify Bank"]
        }
    )
    assert res.status_code == 201, f"Expected 201, got {res.status_code} {res.data}"
    created_report = res.get_json()["report"]
    report_id = created_report["id"]
    print("PASS: Report filed successfully with Ref #:", created_report["reference_number"])

    print("\n=== TEST 6: Fetch My Reports (/api/reports/mine) ===")
    res = client.get("/api/reports/mine", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res.status_code == 200
    my_reports = res.get_json()["reports"]
    assert len(my_reports) >= 1
    print(f"PASS: Fetched {len(my_reports)} user report(s).")

    print("\n=== TEST 7: AI Chatbot Endpoint (/api/ai-crime/chat) ===")
    res = client.post("/api/ai-crime/chat", json={
        "message": "I lost money on UPI, what should I do first?",
        "history": []
    })
    assert res.status_code == 200
    chat_res = res.get_json()
    print("PASS: AI Chat replied:", chat_res.get("reply")[:80] + "...")

    print("\n=== TEST 8: Admin Login & Role Check ===")
    res = client.post("/api/auth/login", json={
        "email": "admin@cybercrime.gov.in",
        "password": "AdminPass123!"
    })
    assert res.status_code == 200
    admin_token = res.get_json()["access_token"]
    print("PASS: Admin logged in successfully.")

    print("\n=== TEST 9: Admin Telemetry Stats (/api/admin/stats) ===")
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    stats = res.get_json()
    print("PASS: Admin stats retrieved. Total cases:", stats["total"], "By severity:", stats["by_severity"])

    print("\n=== TEST 10: Admin Status Workflow (/api/admin/reports/:id) ===")
    res = client.patch(f"/api/admin/reports/{report_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "In Review"}
    )
    assert res.status_code == 200
    updated_rep = res.get_json()["report"]
    assert updated_rep["status"] == "In Review"
    print("PASS: Admin transitioned report status to 'In Review'.")

    print("\n==========================================")
    print("ALL 10 REST API ENDPOINTS TESTED & PASSED!")
    print("==========================================")

if __name__ == "__main__":
    with app.app_context():
        run_tests()
