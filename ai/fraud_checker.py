import os
import re
import json
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv

load_dotenv()

# Common Indian Banking, Fintech & E-commerce Brands for Typosquatting / Impersonation Detection
OFFICIAL_BRAND_DOMAINS = {
    'sbi': ['sbi.co.in', 'onlinesbi.sbi', 'onlinesbi.com'],
    'onlinesbi': ['onlinesbi.sbi', 'onlinesbi.com', 'sbi.co.in'],
    'hdfc': ['hdfcbank.com', 'hdfc.com'],
    'hdfcbank': ['hdfcbank.com'],
    'icici': ['icicibank.com', 'icici.com'],
    'icicibank': ['icicibank.com'],
    'axis': ['axisbank.com'],
    'axisbank': ['axisbank.com'],
    'kotak': ['kotak.com', 'kotakbank.com'],
    'pnb': ['pnbindia.in', 'netpnb.com'],
    'bob': ['bankofbaroda.in', 'bankofbaroda.com'],
    'canara': ['canarabank.com'],
    'paytm': ['paytm.com'],
    'phonepe': ['phonepe.com'],
    'gpay': ['google.com', 'pay.google.com'],
    'googlepay': ['google.com', 'pay.google.com'],
    'bhim': ['bhimupi.org.in', 'npci.org.in'],
    'cred': ['cred.club'],
    'amazon': ['amazon.in', 'amazon.com'],
    'flipkart': ['flipkart.com'],
    'swiggy': ['swiggy.com'],
    'zomato': ['zomato.com'],
    'trai': ['trai.gov.in'],
    'incometax': ['incometax.gov.in', 'incometaxindia.gov.in'],
    'uidai': ['uidai.gov.in'],
    'epfo': ['epfindia.gov.in']
}

SUSPICIOUS_TLDS = {
    '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work', 
    '.click', '.fit', '.rest', '.loan', '.buzz', '.cam', '.live',
    '.quest', '.monster', '.support', '.shop', '.icu', '.site'
}

URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'cutt.ly', 'rb.gy', 
    'shorturl.at', 'ow.ly', 'buff.ly', 'rebrand.ly', 'tiny.cc'
}

SUSPICIOUS_KEYWORDS = [
    'verify', 'kyc', 'pan', 'aadhaar', 'urgent', 'suspended', 
    'blocked', 'refund', 'lottery', 'winner', 'prize', 'claim', 
    'reward', 'login-security', 'update-account', 'bonus', 
    'cashback', 'unauthorized', 'sim-block', 'telecom-kyc'
]

def detect_input_type(text: str) -> str:
    """
    Detects if user input is a URL/domain, a Phone Number, or unknown.
    """
    if not text:
        return "unknown"
    
    clean_text = text.strip()
    
    # 1. Check for URL patterns
    # Starts with http/https or contains domain-like patterns with dot and no spaces
    if re.match(r'^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/.*)?$', clean_text):
        return "url"
    if clean_text.startswith(('http://', 'https://', 'www.')) or re.search(r'^[a-zA-Z0-9-]+\.(com|in|org|net|co|gov|edu|io|xyz|top|site|app|tk|ml|ga|cf|gq)(\/.*)?$', clean_text, re.IGNORECASE):
        return "url"
    # IP address URL
    if re.match(r'^(https?:\/\/)?(\d{1,3}\.){3}\d{1,3}(:\d+)?(\/.*)?$', clean_text):
        return "url"

    # 2. Check for Phone Number patterns (allow +, -, spaces, parentheses)
    digits_only = re.sub(r'[\s\-\(\)\+]', '', clean_text)
    if digits_only.isdigit() and (7 <= len(digits_only) <= 14):
        return "phone"

    return "unknown"

def query_google_safe_browsing(url: str, api_key: str = None) -> dict:
    """
    Queries the official Google Safe Browsing Lookup API (v4 threatMatches:find).
    """
    if not api_key:
        api_key = os.environ.get('GOOGLE_SAFE_BROWSING_API_KEY', '').strip()

    # If key is empty or default placeholder
    if not api_key or api_key == 'un_copy_pannina_key_idha_paste_pannunga':
        return {
            "status": "unavailable",
            "flagged": False,
            "threat_types": [],
            "details": "Google Safe Browsing API key not configured."
        }

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    
    # Ensure proper URL scheme for Google API
    test_url = url.strip()
    if not test_url.startswith(('http://', 'https://')):
        test_url = 'http://' + test_url

    payload = {
        "client": {
            "clientId": "zeroguard-ai",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE", 
                "SOCIAL_ENGINEERING", 
                "UNWANTED_SOFTWARE", 
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [
                {"url": test_url}
            ]
        }
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=6)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            if matches:
                threats = list(set([m.get('threatType', 'THREAT') for m in matches]))
                return {
                    "status": "flagged",
                    "flagged": True,
                    "threat_types": threats,
                    "details": f"Flagged by Google Safe Browsing as a confirmed threat ({', '.join(threats)})."
                }
            else:
                return {
                    "status": "clean",
                    "flagged": False,
                    "threat_types": [],
                    "details": "Not listed in Google Safe Browsing threat database."
                }
        else:
            return {
                "status": "unavailable",
                "flagged": False,
                "threat_types": [],
                "details": f"Google Safe Browsing returned HTTP {response.status_code}."
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "flagged": False,
            "threat_types": [],
            "details": f"Google Safe Browsing check unavailable ({str(e)})."
        }

def check_url_heuristics(url: str) -> dict:
    """
    Evaluates rule-based heuristic patterns for suspicious URLs.
    """
    normalized_url = url.strip()
    if not normalized_url.startswith(('http://', 'https://')):
        normalized_url = 'http://' + normalized_url

    parsed = urlparse(normalized_url)
    hostname = (parsed.hostname or '').lower()
    full_path = (parsed.path + '?' + parsed.query).lower()

    findings = []
    suspicion_score = 0

    # 1. Protocol Check (Plain HTTP)
    if parsed.scheme == 'http':
        findings.append({
            "type": "insecure_protocol",
            "severity": "medium",
            "message": "Uses unencrypted HTTP connection instead of secure HTTPS."
        })
        suspicion_score += 15

    # 2. IP Address in Hostname
    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', hostname):
        findings.append({
            "type": "ip_hostname",
            "severity": "high",
            "message": "Uses direct numeric IP address host instead of a registered domain name."
        })
        suspicion_score += 40

    # 3. Suspicious / Free TLD Check
    matched_tld = None
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            matched_tld = tld
            break
    if matched_tld:
        findings.append({
            "type": "suspicious_tld",
            "severity": "high",
            "message": f"Uses high-risk top-level domain ({matched_tld}) frequently associated with disposable phishing sites."
        })
        suspicion_score += 35

    # 4. URL Shortener Service Check
    for shortener in URL_SHORTENERS:
        if hostname == shortener or hostname.endswith('.' + shortener):
            findings.append({
                "type": "url_shortener",
                "severity": "medium",
                "message": f"Uses URL shortening service ({shortener}) to obfuscate the real destination link."
            })
            suspicion_score += 25
            break

    # 5. Brand Typosquatting / Phishing Impersonation Check
    brand_impersonated = None
    for brand, official_domains in OFFICIAL_BRAND_DOMAINS.items():
        if brand in hostname:
            # Check if it is an authentic domain
            is_official = any(hostname == off or hostname.endswith('.' + off) for off in official_domains)
            if not is_official:
                brand_impersonated = brand
                findings.append({
                    "type": "typosquatting",
                    "severity": "high",
                    "message": f"Impersonates recognized brand '{brand.upper()}' on an unauthorized third-party domain ({hostname})."
                })
                suspicion_score += 45
                break

    # 6. Suspicious Keywords in URL
    matched_keywords = []
    url_lower = normalized_url.lower()
    for kw in SUSPICIOUS_KEYWORDS:
        if re.search(r'[\/\.\-_=]' + re.escape(kw) + r'[\/\.\-_&=]?', url_lower):
            matched_keywords.append(kw)
    
    if matched_keywords:
        findings.append({
            "type": "suspicious_keywords",
            "severity": "medium",
            "message": f"Contains urgency or credential-harvesting keywords ({', '.join(matched_keywords[:3])})."
        })
        suspicion_score += min(len(matched_keywords) * 15, 30)

    # 7. Subdomain Stacking (e.g. sbi.com.login-verify.xyz)
    dot_count = hostname.count('.')
    if dot_count >= 4:
        findings.append({
            "type": "subdomain_stacking",
            "severity": "medium",
            "message": f"Excessive subdomain depth ({dot_count} dots) commonly used to mask malicious hosts."
        })
        suspicion_score += 20

    return {
        "hostname": hostname,
        "suspicion_score": min(suspicion_score, 100),
        "findings": findings
    }

def check_complaint_database_url(url: str, db_session = None) -> dict:
    """
    Cross-references URL against existing complaints in ZeroGuard database.
    """
    clean_url = url.strip().lower()
    if clean_url.startswith(('http://', 'https://')):
        clean_url = clean_url.split('://', 1)[1]
    clean_url = clean_url.rstrip('/')

    domain = clean_url.split('/', 1)[0].split('?')[0]

    match_count = 0
    recent_refs = []

    try:
        from database.models import Complaint
        complaints = Complaint.query.all()
        for c in complaints:
            answers = c.answers or {}
            desc = (c.description or '') + ' ' + (c.original_description or '')
            
            # Check answers fields (e.g. phishing_url)
            found = False
            for k, v in answers.items():
                if isinstance(v, str) and (domain in v.lower() or clean_url in v.lower()):
                    found = True
                    break
            
            if not found and (domain in desc.lower() or clean_url in desc.lower()):
                found = True

            if found:
                match_count += 1
                if c.reference_number not in recent_refs:
                    recent_refs.append(c.reference_number)
    except Exception as e:
        print(f"[DB URL CHECK ERROR] {e}")

    return {
        "match_count": match_count,
        "recent_references": recent_refs[:3]
    }

def check_complaint_database_phone(phone_digits: str, db_session = None) -> dict:
    """
    Cross-references phone number against existing complaints in ZeroGuard database.
    """
    match_count = 0
    recent_refs = []

    try:
        from database.models import Complaint
        complaints = Complaint.query.all()
        for c in complaints:
            answers = c.answers or {}
            desc = (c.description or '') + ' ' + (c.original_description or '')
            
            found = False
            for k, v in answers.items():
                if isinstance(v, str) and phone_digits in re.sub(r'\D', '', v):
                    found = True
                    break
            
            if not found and phone_digits in re.sub(r'\D', '', desc):
                found = True

            if found:
                match_count += 1
                if c.reference_number not in recent_refs:
                    recent_refs.append(c.reference_number)
    except Exception as e:
        print(f"[DB PHONE CHECK ERROR] {e}")

    return {
        "match_count": match_count,
        "recent_references": recent_refs[:3]
    }

def check_url(url: str, api_key: str = None) -> dict:
    """
    Comprehensive multi-source URL safety analysis combining:
    1. Google Safe Browsing API v4
    2. ZeroGuard platform complaint database
    3. Rule-based pattern heuristics
    """
    # 1. Google Safe Browsing
    google_res = query_google_safe_browsing(url, api_key=api_key)
    
    # 2. Platform Database Cross-Reference
    db_res = check_complaint_database_url(url)
    
    # 3. Rule-Based Heuristics
    heuristics_res = check_url_heuristics(url)

    reasons = []
    risk_score = 15

    # Evaluate Google Safe Browsing signal
    if google_res.get('flagged'):
        reasons.append({
            "source": "Google Safe Browsing",
            "severity": "danger",
            "title": "Confirmed Malicious / Phishing URL",
            "description": google_res.get('details', 'Flagged in Google Safe Browsing global threat index.')
        })
        risk_score = max(risk_score, 95)
    elif google_res.get('status') == 'clean':
        reasons.append({
            "source": "Google Safe Browsing",
            "severity": "success",
            "title": "Clean in Google Safe Browsing",
            "description": "No active malware or social engineering reports in Google's threat database."
        })
    else:
        reasons.append({
            "source": "Google Safe Browsing",
            "severity": "muted",
            "title": "Safe Browsing Check Inconclusive",
            "description": google_res.get('details', 'Live Google check unavailable.')
        })

    # Evaluate Complaint Database signal
    if db_res.get('match_count', 0) > 0:
        count = db_res['match_count']
        reasons.append({
            "source": "ZeroGuard Threat Database",
            "severity": "danger" if count >= 2 else "warning",
            "title": f"Reported in {count} ZeroGuard Complaint{'s' if count > 1 else ''}",
            "description": f"This link or domain was cited by citizens in {count} previous cyber incident report{'s' if count > 1 else ''}."
        })
        risk_score = max(risk_score, 70 if count == 1 else 90)
    else:
        reasons.append({
            "source": "ZeroGuard Threat Database",
            "severity": "info",
            "title": "Zero Local Incident Reports",
            "description": "No previous complaints filed on ZeroGuard citing this exact URL."
        })

    # Evaluate Heuristic signals
    for f in heuristics_res.get('findings', []):
        reasons.append({
            "source": "Pattern Heuristics Engine",
            "severity": "danger" if f['severity'] == 'high' else 'warning',
            "title": f['type'].replace('_', ' ').title(),
            "description": f['message']
        })
    
    if heuristics_res.get('suspicion_score', 0) > 0:
        risk_score = max(risk_score, heuristics_res['suspicion_score'])

    # Final Risk Level Mapping
    if risk_score >= 70 or google_res.get('flagged') or db_res.get('match_count', 0) >= 2:
        risk_level = "High"
        summary = "High Risk Detected! Strong indicators of phishing, malware, or fraudulent brand impersonation."
    elif risk_score >= 40 or db_res.get('match_count', 0) == 1:
        risk_level = "Medium"
        summary = "Suspicious Link! Multiple risk heuristics or previous citizen reports detected. Exercise caution."
    else:
        risk_level = "Low"
        summary = "Low Threat Probability. No significant phishing patterns, Google threat flags, or complaint records detected."

    return {
        "input_type": "url",
        "input_value": url,
        "hostname": heuristics_res.get('hostname'),
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "google_safe_browsing": google_res,
        "database_matches": db_res,
        "heuristics": heuristics_res,
        "reasons": reasons
    }

def check_phone_number(phone: str) -> dict:
    """
    Analyzes phone number safety using format validation, known spoof patterns,
    and platform complaint history.
    """
    clean_phone = phone.strip()
    digits = re.sub(r'\D', '', clean_phone)

    # If it starts with 91 and has 12 digits, strip 91 for Indian mobile evaluation
    if len(digits) == 12 and digits.startswith('91'):
        std_digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        std_digits = digits[1:]
    else:
        std_digits = digits

    reasons = []
    risk_score = 15

    # 1. Format & Validity
    is_indian_mobile = (len(std_digits) == 10 and std_digits[0] in {'6', '7', '8', '9'})
    is_toll_free = std_digits.startswith(('1800', '1860'))

    if is_indian_mobile:
        reasons.append({
            "source": "Telecom Pattern Check",
            "severity": "info",
            "title": "Standard Indian Mobile Format",
            "description": f"Valid 10-digit Indian cellular number structure (+91 {std_digits[:5]} {std_digits[5:]})."
        })
    elif is_toll_free:
        reasons.append({
            "source": "Telecom Pattern Check",
            "severity": "info",
            "title": "Toll-Free / Corporate Number",
            "description": "Standard toll-free routing prefix."
        })
    else:
        reasons.append({
            "source": "Telecom Pattern Check",
            "severity": "warning",
            "title": "Non-Standard / International Format",
            "description": "Does not conform to standard 10-digit Indian mobile format. Verify international dial codes."
        })
        risk_score = max(risk_score, 45)

    # 2. Spoofing & Repetitive Pattern Checks
    if len(set(std_digits)) <= 2 and len(std_digits) >= 8:
        reasons.append({
            "source": "Pattern Heuristics Engine",
            "severity": "danger",
            "title": "Repeated Digits / Virtual Number",
            "description": "Highly repetitive digit pattern frequently utilized by automated VoIP dialers."
        })
        risk_score = max(risk_score, 65)

    # 3. Platform Database Cross-Reference
    db_res = check_complaint_database_phone(std_digits)
    if db_res.get('match_count', 0) > 0:
        count = db_res['match_count']
        reasons.append({
            "source": "ZeroGuard Threat Database",
            "severity": "danger" if count >= 2 else "warning",
            "title": f"Flagged in {count} Previous Complaint{'s' if count > 1 else ''}",
            "description": f"This caller number / sender header was cited as a scammer contact in {count} citizen incident report{'s' if count > 1 else ''}."
        })
        risk_score = max(risk_score, 75 if count == 1 else 95)
    else:
        reasons.append({
            "source": "ZeroGuard Threat Database",
            "severity": "info",
            "title": "No Direct Complaint Matches",
            "description": "This phone number has not been previously recorded in ZeroGuard cybercrime complaints."
        })

    # Final Risk Evaluation
    if risk_score >= 70 or db_res.get('match_count', 0) >= 2:
        risk_level = "High"
        summary = "High Risk Contact! Reported in cyber fraud complaints or flagged with suspicious caller patterns."
    elif risk_score >= 40 or db_res.get('match_count', 0) == 1:
        risk_level = "Medium"
        summary = "Suspicious Contact. Unregistered format or prior complaint mentions detected. Never share OTPs or passwords."
    else:
        risk_level = "Low"
        summary = "Standard Number Format. No active incident reports on this platform."

    return {
        "input_type": "phone",
        "input_value": clean_phone,
        "standardized_phone": f"+91 {std_digits}" if is_indian_mobile else clean_phone,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "database_matches": db_res,
        "reasons": reasons
    }
