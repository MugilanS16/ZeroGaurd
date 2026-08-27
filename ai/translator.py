"""
Multi-Language Translation & Localization Module
Supports English (en), Hindi (hi), Tamil (ta), and Telugu (te).
"""

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)',
    'ta': 'தமிழ் (Tamil)',
    'te': 'తెలుగు (Telugu)'
}

UI_TRANSLATIONS = {
    'hi': {
        'step1_title': 'घटना का विवरण (Incident Description)',
        'step1_desc': 'कृपया अपनी भाषा में घटना का पूरा विवरण लिखें। हमारी AI इसे औपचारिक शिकायत में बदल देगी।',
        'step2_title': 'विशिष्ट प्रश्न (Follow-up Questions)',
        'step3_title': 'सुरक्षा निर्देश और साक्ष्य (Guidance & Evidence)',
        'step4_title': 'शिकायत पूर्वावलोकन (Preview Complaint)',
        'step5_title': 'शिकायत दर्ज हो गई (Complaint Submitted)',
        'submit_btn': 'शिकायत दर्ज करें (Submit Report)',
        'ai_polish_btn': 'AI सहायता से सुधारें (Polish with AI)',
        'evidence_label': 'साक्ष्य फ़ाइलें अपलोड करें (Upload Evidence)'
    },
    'ta': {
        'step1_title': 'சம்பவ விவரம் (Incident Description)',
        'step1_desc': 'உங்கள் மொழியில் நடந்த சம்பவத்தை விளக்குங்கள். AI இதனை அதிகாரப்பூர்வ புகாராக மாற்றும்.',
        'step2_title': 'மேலதிக கேள்விகள் (Follow-up Questions)',
        'step3_title': 'பாதுகாப்பு வழிகாட்டுதல் (Guidance & Evidence)',
        'step4_title': 'புகார் முன்னோட்டம் (Preview Complaint)',
        'step5_title': 'புகார் சமர்ப்பிக்கப்பட்டது (Complaint Submitted)',
        'submit_btn': 'புகாரை சமர்ப்பிக்கவும் (Submit Report)',
        'ai_polish_btn': 'AI கொண்டு மெருகூட்டவும் (Polish with AI)',
        'evidence_label': 'ஆதாரங்களை பதிவேற்றவும் (Upload Evidence)'
    },
    'te': {
        'step1_title': 'సంఘటన వివరాలు (Incident Description)',
        'step1_desc': 'మీ భాషలో జరిగిన సంఘటనను వివరించండి. AI దీనిని అధికారిక ఫిర్యాదుగా మారుస్తుంది.',
        'step2_title': 'అదనపు ప్రశ్నలు (Follow-up Questions)',
        'step3_title': 'భద్రతా సూచనలు మరియు ఆధారాలు (Guidance & Evidence)',
        'step4_title': 'ఫిర్యాదు పరిశీలన (Preview Complaint)',
        'step5_title': 'ఫిర్యాదు సమర్పించబడింది (Complaint Submitted)',
        'submit_btn': 'ఫిర్యాదును సమర్పించండి (Submit Report)',
        'ai_polish_btn': 'AI తో సరిచేయండి (Polish with AI)',
        'evidence_label': 'ఆధారాల ఫైళ్లను అప్‌లోడ్ చేయండి (Upload Evidence)'
    },
    'en': {
        'step1_title': 'Incident Description',
        'step1_desc': 'Describe what happened in simple words. Our AI will structure it into a formal police complaint.',
        'step2_title': 'Follow-Up Questions',
        'step3_title': 'Immediate Safety Guidance & Evidence',
        'step4_title': 'Complaint Review & Verification',
        'step5_title': 'Complaint Filed Successfully',
        'submit_btn': 'Submit Verified Complaint',
        'ai_polish_btn': 'Polish & Structure with AI',
        'evidence_label': 'Attach Evidence Files'
    }
}

def get_translation(lang: str, key: str, default: str = '') -> str:
    """Returns localized string for a key."""
    lang_dict = UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS['en'])
    return lang_dict.get(key, default or key)
