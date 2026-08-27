import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app import create_app
from database import db
from database.models import Complaint
from pdf.report_generator import generate_complaint_pdf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_exact_45000_case():
    print("=" * 80)
    print("RUNNING EXACT TEST CASE: financial_loss='yes,45000' with screenshot '₹45,000.00'")
    print("=" * 80)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    test_dir = Path("scratch_45000_test")
    test_dir.mkdir(exist_ok=True)

    # Create image with clear text "₹45,000.00" and "Rs 45,000.00"
    img_path = test_dir / "payment_screenshot_45000.png"
    i = Image.new("RGB", (1000, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(i)
    d.text((50, 50), "Payment Successful", fill=(0, 0, 0))
    d.text((50, 150), "Paid to Merchant: Fraudulent Seller Inc.", fill=(0, 0, 0))
    d.text((50, 250), "Amount Transferred: ₹45,000.00", fill=(0, 128, 0))
    d.text((50, 350), "Transaction ID: 987654321012", fill=(100, 100, 100))
    i.save(img_path, "PNG")

    client = app.test_client()

    with app.app_context():
        # Step 1
        client.get('/report')
        resp1 = client.post('/report', data={
            'language': 'en',
            'raw_description': 'I was scammed online and lost money.',
            'formal_description': 'Online fraud incident.'
        }, follow_redirects=True)

        # Step 2: financial_loss = "yes,45000"
        resp2 = client.post('/report/step2', data={
            'financial_loss': 'yes,45000',
            'bank_name': 'HDFC Bank'
        }, follow_redirects=True)

        # Step 3: Upload screenshot
        with open(img_path, 'rb') as f:
            resp3 = client.post('/report/step3', data={
                'evidence_files': (f, 'payment_screenshot_45000.png'),
                'evidence_categories': 'Screenshot'
            }, follow_redirects=True)

        print(f"\n[STEP 3 RESPONSE CODE]: {resp3.status_code}")

        # Step 5: Final Submission
        resp_submit = client.post('/report/submit', data={
            'guest_email': 'victim45k@example.com'
        }, follow_redirects=True)
        print(f"[SUBMIT RESPONSE CODE]: {resp_submit.status_code}")

        # Fetch saved complaint from DB
        complaint = Complaint.query.order_by(Complaint.id.desc()).first()

        print("\n" + "=" * 80)
        print("DATABASE RECORD RESULTS:")
        if complaint:
            print(f"  Reference Number            : {complaint.reference_number}")
            print(f"  Claimed Amount              : {complaint.claimed_amount}")
            print(f"  Amount Verification Status  : {complaint.amount_verification_status}")
            print(f"  Amount Verification Details : {complaint.amount_verification_details}")

            pdf_path = Path(app.root_path) / "static" / "generated_pdfs" / f"{complaint.reference_number}.pdf"
            print(f"  Generated PDF Path          : {pdf_path}")
            print(f"  PDF File Exists             : {pdf_path.exists()}")
        else:
            print("  ERROR: No complaint found in database!")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    test_exact_45000_case()
