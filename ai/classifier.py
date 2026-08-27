import os
import re
import json
from ai.redact import redact_pii
from ai.prompts import CLASSIFY_PROMPT, ENHANCE_PROMPT
from ai.risk_scorer import calculate_risk_score

CATEGORIES = [
    'Phishing',
    'UPI Fraud',
    'Banking Fraud',
    'Card Fraud',
    'Identity Theft',
    'Social Media Hacking',
    'Email Hacking',
    'Online Shopping Fraud',
    'Job Scam',
    'Investment Scam',
    'Lottery/Prize Scam',
    'Cyber Bullying',
    'Sextortion',
    'Malware/Ransomware',
    'Fake Customer Care Scam'
]

# Comprehensive keyword-based fallback rules
KEYWORD_RULES = {
    'Sextortion': [
        'sextortion', 'nude', 'video call', 'morph', 'naked', 'blackmail', 'leaked video', 
        'intimate photos', 'compromised video', 'threatening to send to family', 'viral video', 'skype call'
    ],
    'UPI Fraud': [
        'upi', 'gpay', 'google pay', 'phonepe', 'paytm', 'bhim', 'qr code', 'scan qr', 
        'cashback', 'collect request', 'vpa', 'pin entered', 'debited via upi', 'money sent on upi'
    ],
    'Phishing': [
        'phishing', 'smishing', 'link', 'fake website', 'fake link', 'sms with link', 
        'clicked link', 'kyc update link', 'pan update link', 'login page clone', 'url', 'credential harvest'
    ],
    'Fake Customer Care Scam': [
        'customer care', 'fake helpline', 'googled helpline', 'toll free number scam', 
        'fake support', 'anydesk', 'teamviewer', 'rustdesk', 'remote access', 'quicksupport'
    ],
    'Job Scam': [
        'job scam', 'part time job', 'telegram task', 'youtube like', 'work from home scam', 
        'prepaid task', 'hotel review task', 'salary deposit', 'vip task', 'freelance scam'
    ],
    'Investment Scam': [
        'crypto', 'bitcoin', 'trading app', 'forex', 'guaranteed returns', 'investment', 
        'stock market tips', '300% profit', 'fake trading platform', 'funds locked'
    ],
    'Banking Fraud': [
        'bank fraud', 'netbanking', 'account hacked', 'unauthorized transfer', 'neft', 
        'rtgs', 'imps', 'fixed deposit broken', 'bank account emptied', 'branch'
    ],
    'Card Fraud': [
        'credit card', 'debit card', 'cvv', 'card skimmed', 'atm fraud', 'card cloned', 
        'international transaction', 'card otp', 'unauthorized swipe'
    ],
    'Social Media Hacking': [
        'instagram hacked', 'facebook hacked', 'whatsapp hacked', 'account takeover', 
        'instagram account stolen', 'impersonating profile', 'reset link sent to hacker'
    ],
    'Email Hacking': [
        'gmail hacked', 'email compromised', 'business email compromise', 'bec', 
        'outlook hacked', 'password changed by intruder', 'forwarding rule set'
    ],
    'Identity Theft': [
        'identity theft', 'aadhaar misuse', 'pan misuse', 'fake loan taken in my name', 
        'sim swap', 'duplicate sim', 'cibil score dropped due to fake loan'
    ],
    'Online Shopping Fraud': [
        'shopping fraud', 'olx', 'quikr', 'fake courier', 'fake website shopping', 
        'ordered product never arrived', 'counterfeit product', 'fake return refund'
    ],
    'Lottery/Prize Scam': [
        'lottery', 'kbc lottery', 'won 25 lakh', 'car prize', 'lucky draw', 
        'customs clearance fee for gift', 'foreign parcel'
    ],
    'Cyber Bullying': [
        'cyber bullying', 'harassment', 'stalking', 'abusive comments', 'trolling', 
        'fake account creating defamation', 'online threat', 'doxxing'
    ],
    'Malware/Ransomware': [
        'ransomware', 'malware', 'virus', 'files encrypted', '.locked', 'trojan', 
        'demanding bitcoin to decrypt', 'device locked', 'spyware'
    ]
}

def classify_by_rules(text: str) -> dict:
    """Fallback rule-based classifier matching keywords and patterns."""
    text_lower = text.lower()
    scores = {cat: 0 for cat in CATEGORIES}
    
    for cat, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if kw in text_lower:
                scores[cat] += 2 if ' ' in kw else 1
                
    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]
    
    if max_score == 0:
        best_cat = 'Banking Fraud' if 'money' in text_lower or 'rupees' in text_lower else 'Phishing'
        confidence = 0.55
    else:
        confidence = min(0.95, 0.60 + (max_score * 0.08))

    risk_info = calculate_risk_score(best_cat, text)
    
    return {
        'crime_type': best_cat,
        'confidence': round(confidence, 2),
        'risk_level': risk_info['level'],
        'risk_score': risk_info['score'],
        'summary': f"Incident classified as {best_cat} with an evaluated {risk_info['level']} risk level.",
        'source': 'Rule-Based Engine'
    }

def classify_incident(raw_description: str) -> dict:
    """Classifies incident using Gemini API if configured, otherwise rule-based fallback."""
    clean_text = redact_pii(raw_description)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"{CLASSIFY_PROMPT}\n\n{clean_text}"
            response = model.generate_content(prompt)
            
            # Extract JSON block
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0].strip()
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1].split('```')[0].strip()
                
            data = json.loads(resp_text)
            crime_type = data.get('crime_type', 'Banking Fraud')
            if crime_type not in CATEGORIES:
                crime_type = 'Banking Fraud'
                
            risk_info = calculate_risk_score(crime_type, clean_text)
            
            return {
                'crime_type': crime_type,
                'confidence': float(data.get('confidence', 0.90)),
                'risk_level': risk_info['level'],
                'risk_score': risk_info['score'],
                'summary': data.get('summary', f'Classified incident as {crime_type}.'),
                'source': 'Gemini AI'
            }
        except Exception:
            # Fall back to rule-based classification gracefully
            pass

    return classify_by_rules(clean_text)

def enhance_description(raw_description: str, language: str = 'en') -> dict:
    """Polishes informal/regional descriptions into formal structured legal drafts."""
    clean_text = redact_pii(raw_description)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"{ENHANCE_PROMPT}\n\nSelected Language Context: {language}\n\n{clean_text}"
            response = model.generate_content(prompt)
            
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0].strip()
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1].split('```')[0].strip()
                
            data = json.loads(resp_text)
            return {
                'formal_description': data.get('formal_description', clean_text),
                'key_facts': data.get('key_facts', []),
                'source': 'Gemini AI'
            }
        except Exception:
            pass

    # Rule-based structured enhancer fallback
    classification = classify_by_rules(clean_text)
    structured_draft = (
        f"COMPLAINT REGARDING INCIDENT OF {classification['crime_type'].upper()}:\n\n"
        f"1. INCIDENT NARRATIVE: The complainant reports a cyber offense wherein the perpetrator "
        f"orchestrated deceptive practices resulting in unauthorized compromise.\n\n"
        f"2. COMPLAINANT STATEMENT: \"{clean_text}\"\n\n"
        f"3. PRELIMINARY TRIAGE: Evaluated as {classification['crime_type']} ({classification['risk_level']} Risk). "
        f"Immediate legal and investigative assistance requested under the IT Act 2000."
    )
    
    return {
        'formal_description': structured_draft,
        'key_facts': [
            f"Crime Type: {classification['crime_type']}",
            f"Evaluated Risk Level: {classification['risk_level']}",
            "Preliminary citizen statement recorded and scrubbed of private credentials."
        ],
        'source': 'Rule-Based Synthesizer'
    }
