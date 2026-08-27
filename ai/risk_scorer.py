import re

# Base category risk weights
CATEGORY_RISK_BASE = {
    'Sextortion': 92,
    'Banking Fraud': 82,
    'UPI Fraud': 76,
    'Phishing': 74,
    'Identity Theft': 75,
    'Card Fraud': 72,
    'Malware/Ransomware': 85,
    'Social Media Hacking': 58,
    'Email Hacking': 60,
    'Investment Scam': 68,
    'Job Scam': 54,
    'Fake Customer Care Scam': 65,
    'Lottery/Prize Scam': 45,
    'Online Shopping Fraud': 38,
    'Cyber Bullying': 50
}

# High-urgency signal patterns
CRITICAL_TRIGGERS = [
    (r'\b(?:blackmail|morph|nude|private video|video call|extort|threatening to viral|send to family|suicide)\b', 25, 'Extortion / Sextortion threats detected'),
    (r'\b(?:just now|happening now|today|within 1 hour|within 2 hours|15 mins ago|golden hour)\b', 15, 'Incident occurred within golden hour window'),
    (r'\b(?:lakh|lakhs|crore|50000|50,000|100000|1,00,000|thousands|huge amount)\b', 18, 'Substantial financial loss indicated'),
    (r'\b(?:police officer|cbi|customs|digital arrest|narcotics|fedex package|arrest warrant)\b', 20, 'Law enforcement impersonation / Digital Arrest intimidation'),
    (r'\b(?:otp shared|password given|anydesk|teamviewer|rustdesk|quicksupport)\b', 16, 'Active device/credential compromise')
]

def calculate_risk_score(crime_type: str, description: str) -> dict:
    """
    Computes a risk score (0-100), risk level (Low/Medium/High/Critical),
    and risk justification signals.
    """
    base_score = CATEGORY_RISK_BASE.get(crime_type, 50)
    score = base_score
    signals = []
    
    desc_lower = (description or '').lower()
    
    # Analyze triggers
    for pattern, boost, reason in CRITICAL_TRIGGERS:
        if re.search(pattern, desc_lower, re.IGNORECASE):
            score += boost
            signals.append(reason)

    # Extract monetary values if present to adjust score
    money_matches = re.findall(r'(?:rs\.?|inr|₹)\s*([\d,]+)', desc_lower)
    for m in money_matches:
        try:
            val = int(m.replace(',', ''))
            if val >= 100000:
                score += 15
                signals.append(f'High-value loss reported: INR {val:,}')
                break
            elif val >= 25000:
                score += 8
                signals.append(f'Moderate loss reported: INR {val:,}')
                break
        except ValueError:
            pass

    # Cap score between 10 and 99
    score = max(15, min(98, score))
    
    # Categorize level
    if score >= 88:
        level = 'Critical'
    elif score >= 70:
        level = 'High'
    elif score >= 45:
        level = 'Medium'
    else:
        level = 'Low'

    return {
        'score': score,
        'level': level,
        'signals': signals if signals else ['Standard risk triage applied']
    }
