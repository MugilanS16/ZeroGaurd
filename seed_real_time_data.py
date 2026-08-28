"""
Seed realistic real-time cybercrime incidents into the SQLite database for testing and demonstration.
"""
from datetime import datetime, timezone, timedelta
import json
from app import app, db, seed_demo_users
from database.models import User, Complaint

REAL_TIME_INCIDENTS = [
    {
        "user_email": "citizen@cybercrime.gov.in",
        "reference_number": "CC-2026-00101",
        "crime_type": "UPI Fraud",
        "severity": "critical",
        "description": "Received an SMS claiming electricity bill overdue. Scammer asked to pay Re 1 via GPay to verify meter number. After entering UPI PIN on the shared link (http://power-bill-update.xyz), Rs 65,000 was debited in 3 transactions to UPI ID billpay987@okaxis.",
        "entities": ["GPay", "http://power-bill-update.xyz", "Rs 65,000", "billpay987@okaxis", "Electricity Bill"],
        "recommended_action": "Call 1930 immediately to freeze beneficiary bank account at Axis Bank.",
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-23"},
            {"question": "Financial Loss (INR)", "answer": "₹65,000"},
            {"question": "Suspect Identifier", "answer": "billpay987@okaxis / +91 9876541230"},
            {"question": "Suspect Platform/URL", "answer": "http://power-bill-update.xyz"}
        ],
        "guidance": [
            "Dial 1930 within the golden hour to flag fraudulent transaction IDs.",
            "Open your UPI app and raise a dispute on all 3 debit alerts.",
            "Block your linked debit card and change UPI PIN immediately."
        ],
        "status": "In Review",
        "days_ago": 1
    },
    {
        "user_email": "citizen@cybercrime.gov.in",
        "reference_number": "CC-2026-00102",
        "crime_type": "Phishing",
        "severity": "high",
        "description": "Got an urgent email purporting to be from Income Tax Department claiming a tax refund of Rs 24,500 was pending. Clicked the embedded portal link (incometax-refund-portal.in) and entered PAN, Aadhaar number, and Netbanking credentials.",
        "entities": ["Income Tax Dept", "Rs 24,500", "incometax-refund-portal.in", "Netbanking", "PAN/Aadhaar"],
        "recommended_action": "Change netbanking password immediately and enable 2FA on email.",
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-22"},
            {"question": "Financial Loss (INR)", "answer": "None (preventative report)"},
            {"question": "Suspect Identifier", "answer": "refunds-notice@it-gov-tax.org"},
            {"question": "Suspect Platform/URL", "answer": "incometax-refund-portal.in"}
        ],
        "guidance": [
            "Log in to official Netbanking and lock internet banking profile password.",
            "Report the phishing email to cert-in at incident@cert-in.org.in.",
            "Monitor CIBIL / credit reports for unauthorized loan enquiries."
        ],
        "status": "Pending",
        "days_ago": 2
    },
    {
        "user_email": "google.user@cybercrime.gov.in",
        "reference_number": "CC-2026-00103",
        "crime_type": "Investment Scam",
        "severity": "high",
        "description": "Joined a Telegram group named 'Institutional Crypto Signals VIP'. Admin @CryptoGuru_Advisor promised 300% weekly returns. Transferred Rs 1,50,000 via IMPS to account in Yes Bank. When attempting to withdraw, admin demanded Rs 40,000 'processing tax' and blocked me.",
        "entities": ["Telegram", "@CryptoGuru_Advisor", "Rs 1,50,000", "Yes Bank", "IMPS"],
        "recommended_action": "File formal FIR and furnish bank transaction statements with UTR numbers.",
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-20"},
            {"question": "Financial Loss (INR)", "answer": "₹1,50,000"},
            {"question": "Suspect Identifier", "answer": "@CryptoGuru_Advisor / Yes Bank A/C 98127391823"},
            {"question": "Suspect Platform/URL", "answer": "t.me/CryptoSignals_VIP"}
        ],
        "guidance": [
            "Export full Telegram chat export with timestamps before account deletion.",
            "Submit UTR numbers to 1930 portal for inter-bank lien marking.",
            "Report scam Telegram channel to Telegram anti-fraud bot."
        ],
        "status": "In Review",
        "days_ago": 4
    },
    {
        "user_email": "digilocker.user@cybercrime.gov.in",
        "reference_number": "CC-2026-00104",
        "crime_type": "Sextortion",
        "severity": "critical",
        "description": "Received an unsolicited video call on Instagram from an unknown account. A morphed explicit video was recorded in 5 seconds. The extortionist is threatening to distribute the video to my Facebook contacts and LinkedIn connections unless Rs 50,000 is sent via PhonePe.",
        "entities": ["Instagram", "PhonePe", "Rs 50,000", "Facebook", "LinkedIn"],
        "recommended_action": "Do NOT pay any ransom. Immediately report to 1930 and local Cyber Cell.",
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-24"},
            {"question": "Financial Loss (INR)", "answer": "₹0 (refused extortion)"},
            {"question": "Suspect Identifier", "answer": "+91 88990 11223 / @insta_glam_2026"},
            {"question": "Suspect Platform/URL", "answer": "instagram.com/insta_glam_2026"}
        ],
        "guidance": [
            "Do NOT transfer any money — paying encourages continuous extortion.",
            "Take screenshots of all threats and extortion messages.",
            "Set all social media profiles to private mode and block caller."
        ],
        "status": "Pending",
        "days_ago": 0
    },
    {
        "user_email": "citizen@cybercrime.gov.in",
        "reference_number": "CC-2026-00105",
        "crime_type": "Social Media Hacking",
        "severity": "medium",
        "description": "My Instagram account with 40,000 followers was compromised after clicking a fake copyright strike email. Hacker changed recovery email and 2FA phone number and is posting cryptocurrency giveaways.",
        "entities": ["Instagram", "Copyright Email", "2FA", "Cryptocurrency"],
        "recommended_action": "Submit video selfie identity verification via Instagram official app.",
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-18"},
            {"question": "Financial Loss (INR)", "answer": "None"},
            {"question": "Suspect Identifier", "answer": "hacked-alert@insta-copyright-notice.com"},
            {"question": "Suspect Platform/URL", "answer": "instagram.com/my_business_official"}
        ],
        "guidance": [
            "Use Instagram hacked account recovery flow with selfie video.",
            "Notify followers via other channels not to click cryptocurrency links.",
            "Check connected Facebook / Meta Business suite access."
        ],
        "status": "Resolved",
        "days_ago": 6
    },
    {
        "user_email": "citizen@cybercrime.gov.in",
        "reference_number": "CC-2026-00106",
        "crime_type": "Online Shopping Fraud",
        "severity": "medium",
        "description": "Ordered a smart LED TV from an advertised website (mega-discounts-india.shop) for Rs 18,999. Payment made via debit card. No tracking details provided and customer care phone is switched off.",
        "entities": ["mega-discounts-india.shop", "Rs 18,999", "Debit Card", "Smart TV"],
        "recommended_action": "File a chargeback request with your card issuing bank for goods not received.",
        "answers": [
            {"question": "Incident Date", "answer": "2026-08-15"},
            {"question": "Financial Loss (INR)", "answer": "₹18,999"},
            {"question": "Suspect Identifier", "answer": "support@mega-discounts-india.shop"},
            {"question": "Suspect Platform/URL", "answer": "https://mega-discounts-india.shop"}
        ],
        "guidance": [
            "Contact your card issuing bank within 30 days to file a chargeback.",
            "Save transaction receipt, invoice, and website screenshots.",
            "File complaint on National Consumer Helpline (NCH 1915)."
        ],
        "status": "Resolved",
        "days_ago": 9
    }
]

def seed_real_time_incidents():
    with app.app_context():
        seed_demo_users()

        for data in REAL_TIME_INCIDENTS:
            user = User.query.filter_by(email=data["user_email"]).first()
            if not user:
                continue

            existing = Complaint.query.filter_by(reference_number=data["reference_number"]).first()
            if not existing:
                created_time = datetime.now(timezone.utc) - timedelta(days=data.get("days_ago", 0))
                c = Complaint(
                    user_id=user.id,
                    reference_number=data["reference_number"],
                    crime_type=data["crime_type"],
                    severity=data["severity"],
                    description=data["description"],
                    entities=json.dumps(data["entities"]),
                    recommended_action=data["recommended_action"],
                    answers=json.dumps(data["answers"]),
                    guidance_text=json.dumps(data["guidance"]),
                    status=data["status"],
                    created_at=created_time,
                    updated_at=created_time
                )
                db.session.add(c)
        db.session.commit()
        print(f"Successfully seeded {len(REAL_TIME_INCIDENTS)} realistic complaints into cybercrime.db!")

if __name__ == "__main__":
    seed_real_time_incidents()
