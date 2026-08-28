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
    'Cyber Bullying': [
        {
            'step_number': 1,
            'title': 'Document All Threatening & Defamatory Posts',
            'action': 'Capture uncropped full-screen screenshots showing user handles, timestamps, profile URLs, and exact abusive/threatening messages.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Do Not Engage or Pay Extortion Demands',
            'action': 'Refrain from replying to hostile messages or transferring money to remove content. Engaging often escalates the harassment.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Report Impersonating / Abusive Profile to Platform',
            'action': 'Use the in-app reporting mechanism on Instagram/Facebook/X for "Impersonation / Harassment" to initiate immediate account takedown.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 4,
            'title': 'Submit Cyber Police Complaint for Cyber Stalking/Defamation',
            'action': 'Lodge this formal report under Section 66D & 67 of the IT Act and relevant IPC/BNS sections at cybercrime.gov.in or local cyber cell.',
            'urgency': 'Within 24h'
        }
    ],
    'Social Media Hacking': [
        {
            'step_number': 1,
            'title': 'Initiate Platform Account Recovery',
            'action': 'Use the official platform recovery tool (e.g. instagram.com/hacked or facebook.com/hacked) using your original email or phone number.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Alert Friends & Family of Impersonation Scam',
            'action': 'Post a public notice via alternative channels warning contacts that your account was compromised and to ignore emergency money requests.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Secure Connected Primary Email & Reset Passwords',
            'action': 'Change your master email account password, revoke active sessions, and activate Authenticator App (TOTP) 2-Factor Authentication.',
            'urgency': 'Immediate'
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
    'Banking Fraud': [
        {
            'step_number': 1,
            'title': 'Emergency Account Freeze via Bank Helpline',
            'action': 'Call your bank fraud helpline immediately to lock Internet Banking, UPI access, and freeze outward beneficiary transactions.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Dial 1930 within Golden Hour',
            'action': 'Report transaction details (Account number, Beneficiary IFSC/Account, IMPS/NEFT UTR) to the National Cybercrime Portal.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Obtain Written Dispute Acknowledgement',
            'action': 'Visit home branch to submit an official unauthorized transaction dispute form under RBI Limited Liability guidelines.',
            'urgency': 'Within 24h'
        }
    ],
    'Card Fraud': [
        {
            'step_number': 1,
            'title': 'Instantly Block Credit / Debit Card',
            'action': 'Open your mobile banking app to toggle OFF international usage, online transactions, and permanently hotlist/block the card.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Raise Chargeback Dispute with Card Issuer',
            'action': 'Call the 24/7 card fraud department to dispute the unauthorized chargeback within 3 days for zero liability protection.',
            'urgency': 'Within 24h'
        }
    ],
    'Identity Theft': [
        {
            'step_number': 1,
            'title': 'Lock Aadhaar Biometrics & Check PAN Activity',
            'action': 'Log in to mAadhaar app / UIDAI portal and enable biometric lock. Check CIBIL / Experian credit reports for unauthorized loan enquiries.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Lodge Police FIR for Stolen / Forged Documents',
            'action': 'File a formal complaint to establish identity theft and protect against liability for fraudulent loans or SIM cards opened in your name.',
            'urgency': 'Within 24h'
        }
    ],
    'Online Shopping Fraud': [
        {
            'step_number': 1,
            'title': 'Dispute Payment with Payment Gateway / Bank',
            'action': 'Contact the payment gateway (Razorpay, Cashfree, Paytm) or card issuer with merchant details to reverse escrow payment.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Preserve Seller Chats & Invoices',
            'action': 'Save product order confirmation, fake tracking IDs, chat conversations, and fake seller contact handles.',
            'urgency': 'Preventive'
        }
    ],
    'Lottery/Prize Scam': [
        {
            'step_number': 1,
            'title': 'Cease Any Clearance / Tax Fee Payments',
            'action': 'Legitimate lotteries never ask winners to pay upfront GST or customs fees. Discontinue all contact with scammers.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Block & Report Fraudulent Numbers to 1930 / Chakshu',
            'action': 'Report the caller numbers and forged prize certificates on DoT Chakshu facility (sancharsaathi.gov.in).',
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
    ],
    'Investment Scam': [
        {
            'step_number': 1,
            'title': 'Stop Additional Fund Transfers',
            'action': 'Scammers will request "tax release fee" or "unfreeze fee". Never pay more money to withdraw locked funds.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Collect Account Numbers & Crypto Wallet Addresses',
            'action': 'Document all bank accounts, UPI IDs, and cryptocurrency wallet hashes where funds were deposited.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Report to SEBI & Cybercrime Portal',
            'action': 'Lodge complaint with SEBI SCORES portal for unregistered brokers and report to 1930 / cybercrime.gov.in.',
            'urgency': 'Within 24h'
        }
    ],
    'Malware/Ransomware': [
        {
            'step_number': 1,
            'title': 'Isolate Infected Devices from Network',
            'action': 'Instantly disconnect ethernet cables and turn off Wi-Fi/Bluetooth to prevent malware lateral propagation across your local network.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Do NOT Pay Ransom Demands',
            'action': 'Ransom payments do not guarantee decryption keys and fund cybercriminal enterprises.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 3,
            'title': 'Check NoMoreRansom.org for Free Decryptors',
            'action': 'Upload sample encrypted files to NoMoreRansom.org (a Europol & Police initiative) to check if decryption keys exist.',
            'urgency': 'Within 24h'
        }
    ],
    'Email Hacking': [
        {
            'step_number': 1,
            'title': 'Revoke Active Sessions & Reset Master Password',
            'action': 'Access your email account settings, terminate all other active sessions, and change master passwords.',
            'urgency': 'Immediate'
        },
        {
            'step_number': 2,
            'title': 'Inspect Mail Forwarding & Filter Rules',
            'action': 'Check email forwarding rules, filters, and auto-reply settings to remove any unauthorized hacker forwarding rules.',
            'urgency': 'Immediate'
        }
    ]
}

# Standard default fallback for remaining categories / Other
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
        'action': 'Report incident details immediately to the National Cybercrime Portal helpline for advisory and coordination.',
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
