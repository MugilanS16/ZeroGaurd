import os
import json
from ai.redact import redact_pii
from ai.prompts import QUESTIONS_PROMPT

# Fallback question banks for all 15 categories
CATEGORY_QUESTIONS_FALLBACK = {
    'UPI Fraud': [
        {'id': 'txn_id', 'question': 'What was the UPI Transaction Reference ID (UTR / RRN number)?', 'placeholder': 'e.g. 234156789012', 'field_type': 'text', 'required': True},
        {'id': 'amount', 'question': 'What was the exact amount debited (in INR)?', 'placeholder': 'e.g. 25,000', 'field_type': 'number', 'required': True},
        {'id': 'suspect_vpa', 'question': 'What was the fraudster’s UPI ID (VPA) or phone number?', 'placeholder': 'e.g. refund-care@upi or 9876543210', 'field_type': 'text', 'required': True},
        {'id': 'bank_name', 'question': 'Which bank account and UPI app (GPay/PhonePe/Paytm) was used?', 'placeholder': 'e.g. SBI via Google Pay', 'field_type': 'text', 'required': False},
        {'id': 'incident_time', 'question': 'Date and approximate time of the transaction:', 'placeholder': 'e.g. 24 Feb 2026, 11:30 AM', 'field_type': 'text', 'required': False}
    ],
    'Sextortion': [
        {'id': 'suspect_contact', 'question': 'What phone number, WhatsApp account, or social handle was used by the extortionist?', 'placeholder': 'e.g. +91 98765 00000 / @fake_user on Instagram', 'field_type': 'text', 'required': True},
        {'id': 'demanded_amount', 'question': 'How much money or cryptocurrency are they demanding?', 'placeholder': 'e.g. INR 50,000 via UPI QR', 'field_type': 'text', 'required': True},
        {'id': 'amount_paid', 'question': 'Did you transfer any amount? (If yes, specify amount and transaction IDs):', 'placeholder': 'e.g. No money paid, or INR 5,000 paid to avoid exposure', 'field_type': 'text', 'required': True},
        {'id': 'platform', 'question': 'Which platforms were involved (WhatsApp, Instagram, Skype, Telegram)?', 'placeholder': 'e.g. Video call on WhatsApp, threats on Instagram', 'field_type': 'text', 'required': False}
    ],
    'Phishing': [
        {'id': 'phishing_url', 'question': 'What was the exact fake website URL or link provided in the message?', 'placeholder': 'e.g. http://sbi-kyc-update-portal.online', 'field_type': 'text', 'required': True},
        {'id': 'sender_header', 'question': 'What was the SMS Sender Header or Email address of the sender?', 'placeholder': 'e.g. AD-SBIBNK or support@banking-update.com', 'field_type': 'text', 'required': True},
        {'id': 'info_entered', 'question': 'What details did you submit on the fake link (Password, Netbanking ID, OTP, Card details)?', 'placeholder': 'e.g. Netbanking username, password, and OTP', 'field_type': 'text', 'required': True},
        {'id': 'financial_loss', 'question': 'Was any unauthorized financial transaction executed?', 'placeholder': 'e.g. Yes, Rs 45,000 debited', 'field_type': 'text', 'required': False}
    ],
    'Banking Fraud': [
        {'id': 'account_number', 'question': 'Bank Name and Last 4 digits of compromised Account Number:', 'placeholder': 'e.g. HDFC Bank A/c ending in 4590', 'field_type': 'text', 'required': True},
        {'id': 'unauthorized_transfers', 'question': 'List of unauthorized transaction amounts and beneficiary details:', 'placeholder': 'e.g. INR 80,000 via IMPS to Axis Bank A/c 987654321', 'field_type': 'text', 'required': True},
        {'id': 'branch_complaint', 'question': 'Did you contact the bank branch or nodal officer to freeze the account?', 'placeholder': 'e.g. Yes, formal dispute ticket #98721 filed', 'field_type': 'text', 'required': False}
    ],
    'Job Scam': [
        {'id': 'recruiter_channel', 'question': 'Which platform/channel did the scammer contact you on (Telegram, WhatsApp, LinkedIn)?', 'placeholder': 'e.g. Telegram group @DailyMediaTasks', 'field_type': 'text', 'required': True},
        {'id': 'task_description', 'question': 'What tasks were promised (e.g. YouTube ratings, hotel reviews, prepaid merchant tasks)?', 'placeholder': 'e.g. Rate 5 YouTube videos for Rs 500 cashback', 'field_type': 'text', 'required': True},
        {'id': 'total_deposited', 'question': 'Total money transferred into scammer accounts / cryptocurrency wallets:', 'placeholder': 'e.g. INR 65,000 across 3 UPI transactions', 'field_type': 'text', 'required': True}
    ],
    'Investment Scam': [
        {'id': 'fake_platform_name', 'question': 'Name of the fake trading app, website, or investment broker:', 'placeholder': 'e.g. ApexCryptoPro.cc / WealthMatrix App', 'field_type': 'text', 'required': True},
        {'id': 'promised_returns', 'question': 'What return on investment was promised?', 'placeholder': 'e.g. 200% profit within 7 days', 'field_type': 'text', 'required': False},
        {'id': 'total_invested', 'question': 'Total amount deposited and account numbers where funds were sent:', 'placeholder': 'e.g. INR 2,50,000 transferred via RTGS', 'field_type': 'text', 'required': True}
    ],
    'Card Fraud': [
        {'id': 'card_type', 'question': 'Card Type & Issuing Bank (Last 4 digits only):', 'placeholder': 'e.g. ICICI Visa Debit Card ending 7812', 'field_type': 'text', 'required': True},
        {'id': 'disputed_amount', 'question': 'Amount and Merchant/Website name of unauthorized charge:', 'placeholder': 'e.g. INR 32,000 at foreign merchant LUXURY-PAY-INTL', 'field_type': 'text', 'required': True},
        {'id': 'card_blocked', 'question': 'Did you immediately block the card via bank app / helpline?', 'placeholder': 'e.g. Yes, blocked within 10 minutes', 'field_type': 'text', 'required': False}
    ],
    'Identity Theft': [
        {'id': 'misused_id', 'question': 'Which identity document was fraudulently misused (Aadhaar, PAN, Voter ID, Passport)?', 'placeholder': 'e.g. PAN card misused for 3 instant loan apps', 'field_type': 'text', 'required': True},
        {'id': 'fraudulent_accounts', 'question': 'Details of unauthorized accounts, loans, or SIM cards opened:', 'placeholder': 'e.g. Loan of Rs 1,20,000 on Dhani App', 'field_type': 'text', 'required': True}
    ],
    'Social Media Hacking': [
        {'id': 'platform_username', 'question': 'Social media platform and compromised account handle/username:', 'placeholder': 'e.g. Instagram: @rahul_sharma_official', 'field_type': 'text', 'required': True},
        {'id': 'linked_email_phone', 'question': 'Original email and phone number linked to the account:', 'placeholder': 'e.g. rahul@example.com / +91-98765-XXXXX', 'field_type': 'text', 'required': True},
        {'id': 'impersonation_activity', 'question': 'Is the hacker posting spam, scams, or requesting money from your followers?', 'placeholder': 'e.g. Asking followers for emergency crypto transfers', 'field_type': 'text', 'required': False}
    ],
    'Email Hacking': [
        {'id': 'email_address', 'question': 'Compromised Email Address and Email Provider:', 'placeholder': 'e.g. director@company.com (Google Workspace)', 'field_type': 'text', 'required': True},
        {'id': 'recovery_status', 'question': 'Have recovery email/phone numbers been altered by the attacker?', 'placeholder': 'e.g. Hacker changed 2FA phone to unknown Russian number', 'field_type': 'text', 'required': True}
    ],
    'Online Shopping Fraud': [
        {'id': 'website_seller', 'question': 'Website URL, Instagram page, or seller contact details:', 'placeholder': 'e.g. www.mega-discount-store.in / @trendz_delhi', 'field_type': 'text', 'required': True},
        {'id': 'order_details', 'question': 'Order ID, Product ordered, and Payment reference:', 'placeholder': 'e.g. Order #8921 for Smartphone - Rs 18,000 paid via UPI', 'field_type': 'text', 'required': True}
    ],
    'Lottery/Prize Scam': [
        {'id': 'scam_mode', 'question': 'How did you receive the prize notification (WhatsApp letter, SMS, Phone call)?', 'placeholder': 'e.g. WhatsApp letter with KBC & Amitabh Bachchan logo', 'field_type': 'text', 'required': True},
        {'id': 'processing_fee_paid', 'question': 'Amount demanded/paid under the guise of taxes, GST, or registration fee:', 'placeholder': 'e.g. Rs 15,000 paid for customs clearance', 'field_type': 'text', 'required': True}
    ],
    'Cyber Bullying': [
        {'id': 'harasser_handles', 'question': 'Usernames, profiles, or phone numbers of perpetrators:', 'placeholder': 'e.g. @anonymous_troll_99 on Twitter / X', 'field_type': 'text', 'required': True},
        {'id': 'nature_of_abuse', 'question': 'Describe the nature of abuse (doxxing, defamatory posts, morphed images, stalking):', 'placeholder': 'e.g. Posted defamatory remarks and phone number online', 'field_type': 'text', 'required': True}
    ],
    'Malware/Ransomware': [
        {'id': 'ransom_extension', 'question': 'File extension appended to encrypted files or malware name:', 'placeholder': 'e.g. .locked / .crypt / README_DECRYPT.txt', 'field_type': 'text', 'required': True},
        {'id': 'ransom_demand', 'question': 'Ransom amount and payment wallet address specified in ransom note:', 'placeholder': 'e.g. 0.2 Bitcoin to wallet bc1q...', 'field_type': 'text', 'required': True}
    ],
    'Fake Customer Care Scam': [
        {'id': 'fake_number_found', 'question': 'Where did you find the fake customer care number (Google Search, Ad, SMS)?', 'placeholder': 'e.g. Top search result on Google for Swiggy Refund Helpline', 'field_type': 'text', 'required': True},
        {'id': 'remote_app_installed', 'question': 'Did the caller ask you to install AnyDesk, TeamViewer, RustDesk, or QuickSupport?', 'placeholder': 'e.g. Asked to install AnyDesk and share 9-digit code', 'field_type': 'text', 'required': True}
    ]
}

def generate_questions(crime_type: str, description: str) -> list:
    """Generates dynamic follow-up questions tailored to the incident using Gemini or fallback."""
    clean_text = redact_pii(description)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = QUESTIONS_PROMPT.format(crime_type=crime_type, description=clean_text)
            response = model.generate_content(prompt)
            
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0].strip()
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1].split('```')[0].strip()
                
            data = json.loads(resp_text)
            questions = data.get('questions', [])
            if questions and len(questions) >= 3:
                return questions
        except Exception:
            pass

    return CATEGORY_QUESTIONS_FALLBACK.get(crime_type, CATEGORY_QUESTIONS_FALLBACK['Phishing'])
