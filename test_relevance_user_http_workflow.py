import os
import sys
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import create_app
from database import db
from database.models import User
from ai.evidence_relevance_checker import check_evidence_relevance, extract_ocr_text_from_image

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
client = app.test_client()

with app.app_context():
    user = User.query.filter_by(email="relevance_tester@zeroguard.ai").first()
    if not user:
        user = User(fullname="Relevance Tester", email="relevance_tester@zeroguard.ai", role="citizen")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()
    user_id = user.id

desc = "I searched for my food delivery app's customer care number on Google and called a number that appeared in the search results. The person asked for remote access to my phone to 'resolve' my issue, and later I found money missing from my bank account."
crime_type = "Fake Customer Care Scam"

wiki_img_path = "scratch_relevance_user_case/tesseract_ocr_wiki.png"

# 2. Authentic Relevant Evidence: Fake Customer Care / AnyDesk / Swiggy Call Screenshot
from PIL import Image, ImageDraw

def create_care_img(filename: str):
    img = Image.new("RGB", (750, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    lines = [
        "Incoming Call: +91 9876543210",
        "Identified as: Food Delivery Customer Care",
        "Agent: Please install AnyDesk remote access tool",
        "Bank Debit Alert: Rs 15,000.00 debited from account"
    ]
    y = 30
    for line in lines:
        draw.text((30, y), line, fill=(0, 0, 0))
        y += 40
    path = Path("scratch_relevance_user_case") / filename
    img.save(path)
    return str(path)

care_img_path = create_care_img("fake_customer_care_proof_15k.png")

print("="*80)
print("COMPREHENSIVE HTTP WIZARD WORKFLOW TEST (USER FAILING CASE)")
print("="*80)

# --------------------------------------------------------------------------
# TEST 1: FAILING CASE (TESSERACT WIKI SCREENSHOT)
# --------------------------------------------------------------------------
print("\n" + "#"*80)
print("TEST 1: SUBMITTING UNRELATED EVIDENCE (TESSERACT OCR WIKI SCREENSHOT)")
print("#"*80)

with client.session_transaction() as sess:
    sess['user_id'] = user_id
    sess['report_draft'] = {
        'language': 'en',
        'raw_description': desc,
        'formal_description': desc,
        'crime_type': crime_type,
        'risk_level': 'High',
        'risk_score': 78,
        'answers': {'app_name': 'Swiggy', 'amount_lost': '15000'},
        'guidance': [],
        'evidence_meta': []
    }

with open(wiki_img_path, 'rb') as f:
    wiki_bytes = f.read()

import io
response_blocked = client.post(
    '/report/step3',
    data={
        'evidence_files': [(io.BytesIO(wiki_bytes), 'tesseract_wiki.png')],
        'evidence_categories': ['Screenshot']
    },
    content_type='multipart/form-data',
    follow_redirects=False
)

html_blocked = response_blocked.data.decode('utf-8')
is_blocked = (response_blocked.status_code == 200)
has_warning_banner = "Unverified Evidence Warning" in html_blocked or "doesn't appear related to your complaint" in html_blocked
has_step4_button = "Proceed to Complaint Preview (Step 4)" in html_blocked

print(f"\n[HTTP RESPONSE VERIFICATION]")
print(f"  HTTP Status Code: {response_blocked.status_code} (200 = Remained on Step 3, 302 = Advanced to Step 4)")
print(f"  Is Blocked on Step 3: {is_blocked}")
print(f"  Contains Error Alert Banner: {has_warning_banner}")
print(f"  Still on Step 3 Page: {has_step4_button}")

assert is_blocked, "FAILED: Expected request to be blocked on Step 3 with status 200!"
assert has_warning_banner, "FAILED: Expected warning alert banner in HTML response!"
print("\n>>> RESULT FOR TEST 1: HARD BLOCK ENFORCED! UNRELATED EVIDENCE CANNOT PROCEED TO STEP 4. <<<")

# --------------------------------------------------------------------------
# TEST 2: POSITIVE CASE (AUTHENTIC FAKE SUPPORT & ANYDESK SCREENSHOT)
# --------------------------------------------------------------------------
print("\n" + "#"*80)
print("TEST 2: SUBMITTING RELEVANT EVIDENCE (FAKE CUSTOMER CARE & ANYDESK SCREENSHOT)")
print("#"*80)

with client.session_transaction() as sess:
    sess['user_id'] = user_id
    sess['report_draft'] = {
        'language': 'en',
        'raw_description': desc,
        'formal_description': desc,
        'crime_type': crime_type,
        'risk_level': 'High',
        'risk_score': 78,
        'answers': {'app_name': 'Swiggy', 'amount_lost': '15000'},
        'guidance': [],
        'evidence_meta': []
    }

with open(care_img_path, 'rb') as f:
    care_bytes = f.read()

response_allowed = client.post(
    '/report/step3',
    data={
        'evidence_files': [(io.BytesIO(care_bytes), 'customer_care_evidence.png')],
        'evidence_categories': ['Screenshot']
    },
    content_type='multipart/form-data',
    follow_redirects=False
)

is_redirected = (response_allowed.status_code == 302)
redirect_target = response_allowed.headers.get('Location', '')

print(f"\n[HTTP RESPONSE VERIFICATION]")
print(f"  HTTP Status Code: {response_allowed.status_code} (302 = Successfully Advanced to Step 4)")
print(f"  Redirect Location: {redirect_target}")
print(f"  Is Allowed to Step 4: {is_redirected and '/report/step4' in redirect_target}")

assert is_redirected and '/report/step4' in redirect_target, "FAILED: Expected redirect to /report/step4!"
print("\n>>> RESULT FOR TEST 2: RELEVANT EVIDENCE SUCCESSFULLY ADVANCES TO STEP 4 (PREVIEW)! <<<")

print("\n" + "="*80)
print("ALL LIVE WORKFLOW TESTS PASSED 100%!")
print("="*80)
