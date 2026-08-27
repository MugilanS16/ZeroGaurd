import os
import json
from ai.redact import redact_pii
from ai.prompts import GUIDANCE_PROMPT

CATEGORY_GUIDANCE_FALLBACK = {
    'UPI Fraud': [
        {
            'step_number': 1,
            'title': 'Call National Cyber Helpline 1930 Immediately',
            'action': 'Dial 1930 within the "Golden Hour" (first 2-3 hours) so nodal cyber officers can place a temporary freeze lien on the suspect beneficiary bank account.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Block & Reset UPI PIN on Payment Apps',
            'action': 'Open your UPI app (GPay, PhonePe, Paytm), unlink the affected bank account temporarily, and change your UPI PIN immediately.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'File Official Dispute with Bank Fraud Wing',
            'action': 'Contact your bank’s 24x7 toll-free fraud helpline to record the dispute reference and obtain a formal transaction dispute ticket.',
            'urgency': 'Within 24h'
        },
        {
            'step_number': 4,
            'title': 'Preserve Screenshot Evidence',
            'action': 'Save uncropped screenshots of the debit SMS, payment app transaction details showing UTR/RRN, and fraudster UPI ID.',
            'urgency': 'Preventive'
        }
    ],
    'Sextortion': [
        {
            'step_number': 1,
            'title': 'Do NOT Transfer Any Money',
            'action': 'Paying extortionists will NOT stop the threats; it only leads to escalated demands. Cease all financial transfers immediately.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Preserve All Evidence Before Blocking',
            'action': 'Take clear screenshots of chat threats, phone numbers, payment QR codes, and profiles before blocking the perpetrator.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Lock & Secure All Social Media Profiles',
            'action': 'Set your Instagram, Facebook, and LinkedIn profiles to Private. Limit message requests from non-friends and hide your followers list.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 4,
            'title': 'Report to Cyber Crime Cell & StopNCII.org',
            'action': 'Register this complaint and generate digital hashes via StopNCII.org to prevent non-consensual media circulation across major tech platforms.',
            'urgency': 'Within 24h'
        }
    ],
    'Phishing': [
        {
            'step_number': 1,
            'title': 'Freeze Compromised Accounts & Cards',
            'action': 'If you entered netbanking passwords or card details on the fake link, call your bank immediately to block netbanking credentials and lock cards.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Change Passwords & Enable Hardware 2FA',
            'action': 'Change master passwords from a separate clean device. Enable authenticator app 2FA (TOTP) instead of SMS-based verification.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Report Phishing Link to CERT-In',
            'action': 'Forward the malicious URL and SMS sender header to incident@cert-in.org.in to trigger domain suspension.',
            'urgency': 'Within 24h'
        }
    ],
    'Fake Customer Care Scam': [
        {
            'step_number': 1,
            'title': 'Uninstall Any Remote Desktop Apps Instantly',
            'action': 'Immediately disconnect your phone from Wi-Fi/data and uninstall AnyDesk, TeamViewer, RustDesk, or QuickSupport apps.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Check Bank Accounts & Freeze Internet Banking',
            'action': 'The fraudster may have captured your screen while you logged into banking. Call bank emergency helpline to freeze online access.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Run Full Antivirus Scan',
            'action': 'Perform a deep malware and rootkit scan on your device or factory-reset if unexpected profile settings were installed.',
            'urgency': 'Within 24h'
        }
    ],
    'Job Scam': [
        {
            'step_number': 1,
            'title': 'Cease All Further Deposits',
            'action': 'Do not make any "VIP activation", "tax clearance", or "withdrawal release" payments. All deposited funds are traps.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Export Full Chat History & Beneficiary Accounts',
            'action': 'Export Telegram/WhatsApp chat history including media, suspect user IDs, and bank account numbers where deposits were sent.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Lodge 1930 & Police Complaint',
            'action': 'Provide beneficiary accounts to Cyber-Cell to aid in money trail mapping and freezing syndicate accounts.',
            'urgency': 'Within 24h'
        }
    ]
}

# Standard default fallback for remaining categories
DEFAULT_GUIDANCE = [
    {
        'step_number': 1,
        'title': 'Preserve Complete Digital Evidence',
        'action': 'Capture screenshots, save chat logs, email headers, transaction references, and caller details in their original unaltered format.',
        'urgency': 'Immediate'
    },
    {
        'step_number': 2,
        'title': 'Dial 1930 Cyber Fraud Helpline',
        'action': 'Report financial aspects immediately to the National Cybercrime Portal helpline for inter-bank coordination.',
        'urgency': 'Immediate'
    },
    {
        'step_number': 3,
        'title': 'Revoke Unauthorized App Permissions & Reset 2FA',
        'action': 'Inspect connected apps on Google/Apple accounts, remove suspicious access permissions, and update login credentials.',
        'urgency': 'Within 24h'
    },
    {
        'step_number': 4,
        'title': 'Submit Verified FIR Complaint',
        'action': 'Download the verified PDF generated from ZeroGuard AI and submit it to your nearest Cyber Crime Police Station or Nodal Cell.',
        'urgency': 'Preventive'
    }
]

def generate_guidance(crime_type: str, description: str) -> list:
    """Generates immediate actionable guidance steps using Gemini or rule-based fallback."""
    clean_text = redact_pii(description)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = GUIDANCE_PROMPT.format(crime_type=crime_type, description=clean_text)
            response = model.generate_content(prompt)
            
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0].strip()
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1].split('```')[0].strip()
                
            data = json.loads(resp_text)
            steps = data.get('steps', [])
            if steps and len(steps) >= 3:
                return steps
        except Exception:
            pass

    return CATEGORY_GUIDANCE_FALLBACK.get(crime_type, DEFAULT_GUIDANCE)
