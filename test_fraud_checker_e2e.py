import os
import sys

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import create_app
from database import db
from database.models import User, Complaint, ActivityLog

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
client = app.test_client()

print("="*80)
print("RUNNING END-TO-END FRAUD CHECKER INTEGRATION TESTS")
print("="*80)

with app.app_context():
    # Setup test complaint to verify DB cross-reference
    existing = Complaint.query.filter_by(reference_number="CC-2026-99991").first()
    if not existing:
        c = Complaint(
            reference_number="CC-2026-99991",
            crime_type="Phishing",
            risk_level="High",
            risk_score=85,
            description="I was sent a fake link http://hdfc-netbanking-verify.xyz/login requesting netbanking password.",
            answers={'phishing_url': 'http://hdfc-netbanking-verify.xyz/login', 'sender_header': '9898989898'},
            status="Pending"
        )
        db.session.add(c)
        db.session.commit()

# 1. Test GET /fraud-checker
print("\n--- TEST 1: Page Render (GET /fraud-checker) ---")
res_page = client.get('/fraud-checker')
assert res_page.status_code == 200, f"Expected 200, got {res_page.status_code}"
assert b"Fraud URL & Phone Number Checker" in res_page.data
print("✓ /fraud-checker renders successfully without requiring authentication.")

# 2. Test Safe URL Scan
print("\n--- TEST 2: Legitimate URL Check (https://www.google.com) ---")
res_safe = client.post('/api/fraud-checker/check', json={'input': 'https://www.google.com'})
assert res_safe.status_code == 200, f"Expected 200, got {res_safe.status_code}"
data_safe = res_safe.get_json()['data']
print(f"Target: {data_safe['input_value']} -> Risk: {data_safe['risk_level']} (Score: {data_safe['risk_score']})")
assert data_safe['risk_level'] == "Low", f"Expected Low, got {data_safe['risk_level']}"
print("✓ Legitimate URL classified as Low Risk.")

# 3. Test Typosquatted Phishing URL
print("\n--- TEST 3: Typosquatted Bank Phishing URL (http://sbi-verify-kyc.tk/update) ---")
res_phish = client.post('/api/fraud-checker/check', json={'input': 'http://sbi-verify-kyc.tk/update'})
assert res_phish.status_code == 200, f"Expected 200, got {res_phish.status_code}"
data_phish = res_phish.get_json()['data']
print(f"Target: {data_phish['input_value']} -> Risk: {data_phish['risk_level']} (Score: {data_phish['risk_score']})")
print("Flagged Reasons:")
for r in data_phish['reasons']:
    print(f"  [{r['source']}] {r['title']}: {r['description']}")
assert data_phish['risk_level'] == "High", f"Expected High, got {data_phish['risk_level']}"
print("✓ Typosquatted .tk phishing link classified as High Risk.")

# 4. Test Complaint Database Cross-Reference
print("\n--- TEST 4: Platform DB Match (hdfc-netbanking-verify.xyz) ---")
res_db = client.post('/api/fraud-checker/check', json={'input': 'http://hdfc-netbanking-verify.xyz/login'})
assert res_db.status_code == 200
data_db = res_db.get_json()['data']
print(f"DB Match Count: {data_db['database_matches']['match_count']}")
assert data_db['database_matches']['match_count'] >= 1, "Expected match in complaint database"
print("✓ URL cross-referenced against existing ZeroGuard complaints.")

# 5. Test Phone Number Scan
print("\n--- TEST 5: Phone Number Scan (+91 9898989898) ---")
res_phone = client.post('/api/fraud-checker/check', json={'input': '+91 9898989898'})
assert res_phone.status_code == 200
data_phone = res_phone.get_json()['data']
print(f"Phone: {data_phone['input_value']} -> Type: {data_phone['input_type']}, Risk: {data_phone['risk_level']}")
assert data_phone['input_type'] == "phone"
assert data_phone['database_matches']['match_count'] >= 1
print("✓ Phone number correctly identified and matched against complaint database.")

# 6. Test Google Safe Browsing Official Test URL
print("\n--- TEST 6: Google Safe Browsing Official Test URL ---")
res_gsb = client.post('/api/fraud-checker/check', json={'input': 'http://testsafebrowsing.appspot.com/s/phishing.html'})
assert res_gsb.status_code == 200
data_gsb = res_gsb.get_json()['data']
print(f"GSB Test URL Risk: {data_gsb['risk_level']}")
print(f"GSB Service Status: {data_gsb['google_safe_browsing']['status']} ({data_gsb['google_safe_browsing']['details']})")

print("\n" + "="*80)
print("ALL FRAUD CHECKER E2E TESTS PASSED 100%!")
print("="*80)
