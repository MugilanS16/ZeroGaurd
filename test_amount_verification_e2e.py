import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from app import create_app
from database import db
from database.models import Complaint, User

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_e2e_tests():
    print("=" * 70)
    print("STARTING E2E EVIDENCE AMOUNT VERIFICATION & OCR INTEGRATION TEST")
    print("=" * 70)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    test_dir = Path("scratch_amount_e2e_images")
    test_dir.mkdir(exist_ok=True)

    # 1. Create screenshot 5000
    img_5000 = test_dir / "receipt_5000.png"
    i1 = Image.new("RGB", (800, 600), color=(255, 255, 255))
    d1 = ImageDraw.Draw(i1)
    d1.text((50, 50), "GPay Payment Successful", fill=(0, 0, 0))
    d1.text((50, 200), "Amount Transferred: Rs. 5,000.00", fill=(0, 128, 0))
    i1.save(img_5000, "PNG")

    # 2. Create screenshot 500
    img_500 = test_dir / "receipt_500.png"
    i2 = Image.new("RGB", (800, 600), color=(255, 255, 255))
    d2 = ImageDraw.Draw(i2)
    d2.text((50, 50), "GPay Payment Successful", fill=(0, 0, 0))
    d2.text((50, 200), "Amount Transferred: Rs. 500.00", fill=(0, 128, 0))
    i2.save(img_500, "PNG")

    client = app.test_client()

    with app.app_context():
        # -------------------------------------------------------------
        # TEST 1: Claimed ₹5000, Evidence ₹5000 -> VERIFIED
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing Claimed ₹5000 vs Evidence ₹5000 (EXPECT: VERIFIED)...")
        # Step 1
        client.post('/report', data={
            'language': 'en',
            'raw_description': 'I lost ₹5000 in a UPI phishing scam after clicking a fake bank link.',
            'formal_description': 'Incident involving unauthorized transfer of Rs. 5,000 via phishing link.'
        }, follow_redirects=True)

        # Step 2
        client.post('/report/step2', data={'bank_name': 'HDFC', 'transaction_id': 'TXN12345'}, follow_redirects=True)

        # Step 3 with Evidence File
        with open(img_5000, 'rb') as f:
            resp3 = client.post('/report/step3', data={
                'evidence_files': (f, 'receipt_5000.png'),
                'evidence_categories': 'Screenshot'
            }, follow_redirects=True)

        assert b'Step 4 of 5' in resp3.data or b'step4' in resp3.data, "Should proceed to Step 4 when amount is verified"
        
        # Step 5 Submit
        resp_sub = client.post('/report/submit', data={'guest_email': 'victim1@example.com'}, follow_redirects=True)
        complaint1 = Complaint.query.order_by(Complaint.id.desc()).first()
        
        assert complaint1 is not None
        assert complaint1.amount_verification_status == 'Verified', f"Expected Verified, got {complaint1.amount_verification_status}"
        assert complaint1.claimed_amount == 5000.0
        print(f"  -> Complaint {complaint1.reference_number}: Status='{complaint1.amount_verification_status}', Claimed=₹{complaint1.claimed_amount:.0f} (PASSED)")

        # -------------------------------------------------------------
        # TEST 2: Claimed ₹50000, Evidence ₹500 -> MISMATCH BLOCKED
        # -------------------------------------------------------------
        print("\n[TEST 2] Testing Claimed ₹50000 vs Evidence ₹500 (EXPECT: MISMATCH BLOCKED)...")
        client.get('/report/step1') # Reset draft
        client.post('/report', data={
            'language': 'en',
            'raw_description': 'I lost ₹50000 in an online investment scheme.',
            'formal_description': 'Unauthorized fraudulent debit of Rs. 50,000.'
        }, follow_redirects=True)
        client.post('/report/step2', data={}, follow_redirects=True)

        with open(img_500, 'rb') as f:
            resp_mismatch = client.post('/report/step3', data={
                'evidence_files': (f, 'receipt_500.png'),
                'evidence_categories': 'Screenshot'
            }, follow_redirects=False)

        # Step 3 should re-render step 3 (HTTP 200) instead of redirecting (HTTP 302) due to mismatch
        assert resp_mismatch.status_code == 200, f"Expected 200 (re-render Step 3 on warning), got {resp_mismatch.status_code}"
        assert b'Evidence Amount Mismatch Warning' in resp_mismatch.data or b'couldn' in resp_mismatch.data, "Mismatch warning text missing"
        print("  -> Mismatch warning displayed and redirect blocked (PASSED)")

        # -------------------------------------------------------------
        # TEST 3: No Amount Mentioned -> N/A (SKIPPED SILENTLY)
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing Cyber Harassment (No Amount Mentioned) (EXPECT: N/A)...")
        client.post('/report', data={
            'language': 'en',
            'raw_description': 'Someone hacked my social media account and is sending unauthorized messages.',
            'formal_description': 'Account takeover and cyber harassment incident.'
        }, follow_redirects=True)
        client.post('/report/step2', data={}, follow_redirects=True)

        with open(img_5000, 'rb') as f:
            resp_na = client.post('/report/step3', data={
                'evidence_files': (f, 'receipt_5000.png'),
                'evidence_categories': 'Screenshot'
            }, follow_redirects=True)

        assert b'Step 4 of 5' in resp_na.data or b'step4' in resp_na.data, "Should proceed to Step 4 when no amount is claimed"
        
        client.post('/report/submit', data={'guest_email': 'victim3@example.com'}, follow_redirects=True)
        complaint3 = Complaint.query.order_by(Complaint.id.desc()).first()

        assert complaint3 is not None
        assert complaint3.amount_verification_status == 'N/A', f"Expected N/A, got {complaint3.amount_verification_status}"
        print(f"  -> Complaint {complaint3.reference_number}: Status='{complaint3.amount_verification_status}' (PASSED)")

        print("\n" + "=" * 70)
        print("ALL END-TO-END EVIDENCE AMOUNT VERIFICATION TESTS PASSED 100%!")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    run_e2e_tests()
