import os
import sys
import io
from pathlib import Path
from PIL import Image, ImageDraw

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import create_app
from database import db
from database.models import User, Complaint

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
client = app.test_client()

TEST_DIR = Path("scratch_relevance_e2e_images")
TEST_DIR.mkdir(parents=True, exist_ok=True)

def create_image_bytes(text: str):
    img = Image.new("RGB", (700, 350), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    lines = text.split("\n")
    y = 30
    for line in lines:
        draw.text((30, y), line, fill=(0, 0, 0))
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

print("="*80)
print("RUNNING END-TO-END FLASK WIZARD EVIDENCE RELEVANCE TESTS")
print("="*80)

with app.app_context():
    # Setup test user
    user = User.query.filter_by(email="relevance_tester@zeroguard.ai").first()
    if not user:
        user = User(fullname="Relevance Tester", email="relevance_tester@zeroguard.ai", role="citizen")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()

    user_id = user.id

# Test 1: Hard Block on Unrelated Evidence
print("\n" + "-"*75)
print("E2E SCENARIO 1: Unrelated Evidence Uploaded -> MUST HARD-BLOCK AT STEP 3")
print("-"*75)

with client.session_transaction() as sess:
    sess['user_id'] = user_id
    sess['report_draft'] = {
        'language': 'en',
        'raw_description': 'I was scammed out of money via Google Pay UPI payment QR scam.',
        'formal_description': 'I was scammed out of money via Google Pay UPI payment QR scam.',
        'crime_type': 'UPI Fraud',
        'risk_level': 'High',
        'risk_score': 76,
        'answers': {},
        'guidance': [],
        'evidence_meta': []
    }

unrelated_file = (create_image_bytes("Strawberry Jam Recipe\nSugar and Lemon Juice\nNutrition 50 Calories"), "recipe.png")

response = client.post(
    '/report/step3',
    data={
        'evidence_files': [unrelated_file],
        'evidence_categories': ['Screenshot']
    },
    content_type='multipart/form-data',
    follow_redirects=False
)

print(f"Response Status Code: {response.status_code} (200 = Stayed on Step 3 with Block/Warning, 302 = Redirected)")
assert response.status_code == 200, f"Expected 200 (Blocked on Step 3), got {response.status_code}"
assert b"Unverified Evidence Warning" in response.data or b"doesn't appear related" in response.data
print("-> E2E SCENARIO 1 PASSED (Correctly Hard-Blocked at Step 3 with Unverified Evidence Warning)")

# Test 2: Relevant Evidence Allowed Through
print("\n" + "-"*75)
print("E2E SCENARIO 2: Relevant Evidence Uploaded -> MUST PROCEED TO STEP 4")
print("-"*75)

with client.session_transaction() as sess:
    sess['user_id'] = user_id
    sess['report_draft'] = {
        'language': 'en',
        'raw_description': 'I was scammed out of money via Google Pay UPI payment QR scam.',
        'formal_description': 'I was scammed out of money via Google Pay UPI payment QR scam.',
        'crime_type': 'UPI Fraud',
        'risk_level': 'High',
        'risk_score': 76,
        'answers': {},
        'guidance': [],
        'evidence_meta': []
    }

upi_file = (create_image_bytes("GPay Payment Successful\nPaid to Merchant Cyber Store\nUPI Ref No 428192019281\nAmount: Rs 5,000.00"), "upi_slip.png")

response2 = client.post(
    '/report/step3',
    data={
        'evidence_files': [upi_file],
        'evidence_categories': ['Screenshot']
    },
    content_type='multipart/form-data',
    follow_redirects=False
)

print(f"Response Status Code: {response2.status_code} (302 = Redirected to Step 4)")
assert response2.status_code == 302, f"Expected 302 (Redirected to Step 4), got {response2.status_code}"
assert '/report/step4' in response2.headers.get('Location', '')
print("-> E2E SCENARIO 2 PASSED (Relevant Evidence Allowed Directly to Step 4)")

print("\n" + "="*80)
print("ALL E2E INTEGRATION TESTS PASSED 100%!")
print("="*80)
