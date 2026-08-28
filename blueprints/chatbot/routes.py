import os
import re
import json
from flask import render_template, request, jsonify, session, current_app
from blueprints.chatbot import chatbot_bp
from extensions import csrf
from ai.redact import redact_pii
from ai.classifier import classify_by_rules
from ai.prompts import CHATBOT_SYSTEM_PROMPT

# Multi-Language Quick Suggestions & Translated Fallback Knowledge
SUGGESTIONS_BY_LANG = {
    'en': [
        'How do I report UPI fraud?',
        'What should I do for Sextortion blackmail?',
        'What is the 1930 helpline?',
        'How to file an official complaint?'
    ],
    'hi': [
        'यूपीआई धोखाधड़ी की रिपोर्ट कैसे करें?',
        'सेक्सटॉर्शन और ब्लैकमेल में क्या करें?',
        '1930 हेल्पलाइन क्या है?',
        'आधिकारिक शिकायत कैसे दर्ज करें?'
    ],
    'ta': [
        'யுபிஐ மோசடியைப் புகார் செய்வது எப்படி?',
        'செக்ஸ்டார்ஷன் மிரட்டலுக்கு என்ன செய்ய வேண்டும்?',
        '1930 உதவி எண் என்றால் என்ன?',
        'அதிகாரப்பூர்வ புகாரை அளிப்பது எப்படி?'
    ],
    'te': [
        'యుపిఐ మోసాన్ని ఎలా నివేదించాలి?',
        'సెక్స్‌టార్షన్ బ్లాక్‌మెయిల్‌కు ఏమి చేయాలి?',
        '1930 హెల్ప్‌లైన్ అంటే ఏమిటి?',
        'అధికారిక ఫిర్యాదును ఎలా నమోదు చేయాలి?'
    ]
}

TOPIC_KNOWLEDGE_TRANSLATIONS = {
    'hi': {
        'helpline': """वित्तीय साइबर धोखाधड़ी से सुरक्षा के लिए तुरंत कार्रवाई करें:<br/><br/>
<strong>राष्ट्रीय साइबर अपराध आपातकालीन हेल्पलाइन 1930:</strong><br/>
• <strong>यह क्या करता है:</strong> नागरिकों को सीधे नागरिक वित्तीय साइबर धोखाधड़ी रिपोर्टिंग और प्रबंधन प्रणाली (CFCFRMS) से जोड़ता है।<br/>
• <strong>गोल्डन आवर (पहले 2-3 घंटे):</strong> यदि आप घटना के 2-3 घंटे के भीतर 1930 पर रिपोर्ट करते हैं, तो नोडल अधिकारी धोखाधड़ी की गई राशि को एटीएम निकासी या हस्तांतरण से पहले तुरंत फ्रीज कर सकते हैं।<br/>
• <strong>आवश्यक जानकारी:</strong> अपना बैंक खाता नंबर, डेबिट कार्ड अंतिम 4 अंक, संदिग्ध यूपीआई आईडी और यूटीआर नंबर तैयार रखें।""",
        
        'upi': """संदिग्ध यूपीआई लेनदेन के लिए तत्काल सुरक्षा कदम:<br/><br/>
<strong>यूपीआई और क्यूआर कोड धोखाधड़ी के नियम:</strong><br/>
1. <strong>पैसे प्राप्त करने के लिए कभी भी पिन (PIN) दर्ज न करें:</strong> यूपीआई पिन केवल पैसे भेजने के लिए आवश्यक होता है, कैशबैक या रिफंड प्राप्त करने के लिए कभी नहीं।<br/>
2. <strong>तुरंत 1930 पर कॉल करें:</strong> 12-अंकीय यूटीआर/आरआरएन नंबर रिपोर्ट करें।<br/>
3. <strong>ऐप में शिकायत दर्ज करें:</strong> गूगल पे/फोनपे/पेटीएम में ट्रांजैक्शन हिस्ट्री &rarr; "रिपोर्ट फ्रॉड" पर क्लिक करें।<br/>
4. <strong>यूपीआई पिन बदलें:</strong> सुरक्षा के लिए अपने सभी बैंक खातों का यूपीआई पिन तुरंत रीसेट करें।""",

        'sextort': """सेक्सटॉर्शन और ऑनलाइन ब्लैकमेल के लिए महत्वपूर्ण मार्गदर्शन:<br/><br/>
<strong>कृपया घबराएं नहीं और पैसे न भेजें:</strong><br/>
1. <strong>पैसे बिल्कुल न भेजें:</strong> ब्लैकमेलर को पैसे देने से वह वीडियो डिलीट नहीं करता, बल्कि और अधिक पैसे की मांग करता है।<br/>
2. <strong>चैट डिलीट न करें:</strong> धमकी भरे संदेशों, फोन नंबर, यूपीआई क्यूआर और सोशल मीडिया हैंडल के स्क्रीनशॉट सुरक्षित रखें।<br/>
3. <strong>सोशल मीडिया प्रोफाइल लॉक करें:</strong> अपने इंस्टाग्राम, फेसबुक और लिंक्डइन प्रोफाइल को तुरंत प्राइवेट करें।<br/>
4. <strong>StopNCII.org का उपयोग करें:</strong> यह टूल आपत्तिजनक मीडिया के हैश जनरेट करके उन्हें सोशल मीडिया पर अपलोड होने से रोकता है।<br/>
5. <strong>कानूनी सुरक्षा:</strong> आईटी एक्ट की धारा 67A और बीएनएस के तहत यह एक गंभीर अपराध है। हमारे 5-स्टेप विजार्ड से तुरंत शिकायत दर्ज करें।""",

        'rbi': """आरबीआई (RBI) शून्य ग्राहक देयता नीति (Zero Liability Policy):<br/><br/>
• <strong>3 कार्य दिवसों के भीतर:</strong> यदि अनधिकृत लेनदेन तृतीय-पक्ष सुरक्षा उल्लंघन के कारण होता है और आप 3 कार्य दिवसों के भीतर बैंक को सूचित करते हैं, तो आपकी <strong>शून्य देयता (Zero Liability)</strong> होगी और बैंक पूरा रिफंड देगा।<br/>
• <strong>4 से 7 कार्य दिवसों के भीतर:</strong> ग्राहक की अधिकतम देयता ₹10,000 (बचत खाता) या ₹25,000 तक सीमित है।<br/>
<em>हमेशा अपने बैंक शाखा से लिखित शिकायत पावती (Acknowledgement Ticket) प्राप्त करें!</em>""",

        'wizard': """ZeroGuard AI 5-स्टेप शिकायत रिपोर्टिंग प्रक्रिया:<br/><br/>
• <strong>स्टेप 1 (घटना विवरण):</strong> हिंदी, अंग्रेजी, तमिल या तेलुगु में घटना लिखें। AI लाइव जोखिम स्कोर प्रदान करेगा।<br/>
• <strong>स्टेप 2 (अनुवर्ती प्रश्न):</strong> धोखाधड़ी से जुड़े विशिष्ट प्रश्नों के उत्तर दें (यूटीआर, संदिग्ध नंबर)।<br/>
• <strong>स्टेप 3 (सुरक्षा निर्देश व साक्ष्य):</strong> आपातकालीन सुरक्षा निर्देश देखें और साक्ष्य स्क्रीनशॉट संलग्न करें।<br/>
• <strong>स्टेप 4 (पूर्वावलोकन):</strong> गोपनीय जानकारी रहित शिकायत पत्र की समीक्षा करें।<br/>
• <strong>स्टेप 5 (पीडीएफ डाउनलोड):</strong> पुलिस-रेडी आधिकारिक एफआईआर संदर्भ शिकायत रिपोर्ट (PDF) डाउनलोड करें।""",

        'anydesk': """फर्जी कस्टमर केयर और रिमोट ऐप अलर्ट:<br/><br/>
1. <strong>इंटरनेट बंद करें और ऐप अनइंस्टॉल करें:</strong> तुरंत वाई-फाई/मोबाइल डेटा बंद करें और AnyDesk, TeamViewer, या RustDesk को अनइंस्टॉल करें।<br/>
2. <strong>बैंकिंग ब्लॉक करें:</strong> जालसाज स्क्रीन शेयरिंग से ओटीपी देख लेते हैं। अपने बैंक को कॉल करके नेटबैंकिंग ब्लॉक करवाएं।<br/>
3. <strong>सावधानी:</strong> असली बैंक कस्टमर केयर कभी भी रिमोट ऐप डाउनलोड करने के लिए नहीं कहते!""",

        'telegram': """पार्ट-टाइम जॉब और टेलीग्राम टास्क स्कैम:<br/><br/>
• <strong>कार्यप्रणाली:</strong> जालसाज यूट्यूब वीडियो लाइक करने के लिए ₹150-500 का लालच देते हैं। शुरुआती भुगतान के बाद वे "वीआईपी टास्क" के नाम पर ₹10,000+ जमा करवाते हैं और पैसे ब्लॉक कर देते हैं।<br/>
• <strong>सुरक्षा कार्रवाई:</strong> आगे कोई पैसा जमा न करें। चैट लॉग और यूपीआई आईडी के स्क्रीनशॉट लेकर तुरंत 1930 या हमारे पोर्टल पर शिकायत दर्ज करें।"""
    },
    'ta': {
        'helpline': """நிதி சைபர் மோசடியில் இருந்து மீள உடனடி நடவடிக்கை எடுக்கவும்:<br/><br/>
<strong>தேசிய சைபர் குற்ற அவசர உதவி எண் 1930:</strong><br/>
• <strong>இதன் பணி:</strong> குடிமக்களை நேரடியாக குடிமக்கள் நிதி சைபர் மோசடி புகாரளிப்பு அமைப்புடன் (CFCFRMS) இணைக்கிறது.<br/>
• <strong>பொற்காலம் (முதல் 2-3 மணிநேரம்):</strong> பண இழப்பு ஏற்பட்ட 2-3 மணிநேரத்திற்குள் 1930க்கு அழைத்தால், அதிகாரிகள் திருடப்பட்ட பணத்தை உடனடியாக முடக்க முடியும்.<br/>
• <strong>தயாராக வைக்க வேண்டியவை:</strong> வங்கி கணக்கு எண், டெபிட் கார்டு கடைசி 4 இலக்கங்கள், சந்தேக நபரின் UPI ID மற்றும் UTR எண்.""",
        
        'upi': """UPI மற்றும் QR குறியீடு மோசடிக்கான உடனடி பாதுகாப்பு முறைகள்:<br/><br/>
1. <strong>பணம் பெற UPI PIN பதிவிட வேண்டாம்:</strong> UPI PIN பணம் அனுப்ப மட்டுமே தேவைப்படும், பணத்தை அல்லது ரீஃபண்ட் பெற ஒருபோதும் தேவைப்படாது.<br/>
2. <strong>உடனடியாக 1930க்கு அழைக்கவும்:</strong> 12 இலக்க UTR/RRN எண்ணைப் புகாரளிக்கவும்.<br/>
3. <strong>செயலியில் புகார் அளிக்கவும்:</strong> GPay/PhonePe/Paytm செயலியில் பரிவர்த்தனை வரலாறு சென்று புகாரைப் பதிவு செய்யவும்.<br/>
4. <strong>UPI PIN மாற்றவும்:</strong> உங்கள் வங்கி கணக்குகளின் UPI PIN ஐ உடனடியாக மாற்றவும்.""",

        'sextort': """செக்ஸ்டார்ஷன் மற்றும் ஆன்லைன் மிரட்டலுக்கான அவசர வழிகாட்டுதல்:<br/><br/>
<strong>தயவுசெய்து பதற்றமடைய வேண்டாம், பணம் அனுப்ப வேண்டாம்:</strong><br/>
1. <strong>பணம் அனுப்ப வேண்டாம்:</strong> மிரட்டுபவருக்கு பணம் அனுப்புவது வீடியோவை நீக்காது, மேலும் அதிக பணம் கேட்க மட்டுமே வழிவகுக்கும்.<br/>
2. <strong>சாட்களை நீக்க வேண்டாம்:</strong> மிரட்டல் செய்திகள், போன் எண், UPI QR ஆகியவற்றின் ஸ்கிரீன்ஷாட்களை சேமித்து வைக்கவும்.<br/>
3. <strong>சமூக வலைத்தள பூட்டு:</strong> இன்ஸ்டாகிராம், பேஸ்புக் கணக்குகளை உடனடியாக 'Private' ஆக மாற்றவும்.<br/>
4. <strong>StopNCII.org பயன்படுத்தவும்:</strong> இந்த தளம் உங்கள் புகைப்படங்கள் இணையத்தில் பரவுவதைத் தடுக்கிறது.<br/>
5. <strong>சட்டப் பாதுகாப்பு:</strong> IT சட்டம் பிரிவு 67A இன் கீழ் இது தீவிர குற்றமாகும். நமது 5-படி வழிகாட்டி மூலம் உடனடியாக புகார் அளிக்கவும்.""",

        'rbi': """ரிசர்வ் வங்கி (RBI) பூஜ்ஜிய வாடிக்கையாளர் பொறுப்பு விதி:<br/><br/>
• <strong>3 வேலை நாட்களுக்குள்:</strong> உங்கள் தவறு இல்லாமல் நடந்த மோசடியை 3 நாட்களுக்குள் வங்கிக்கு அறிவித்தால், உங்களுக்கு <strong>பூஜ்ஜிய பொறுப்பு (Zero Liability)</strong> பொருந்தும், வங்கி முழு தொகையையும் திரும்ப வழங்கும்.<br/>
• <strong>4 முதல் 7 நாட்களுக்குள்:</strong> அதிகபட்ச பொறுப்பு ₹10,000 வரை மட்டுமே.<br/>
<em>எப்போதும் உங்கள் வங்கி கிளையிலிருந்து அதிகாரப்பூர்வ புகார் ரசீதைப் (Acknowledgement Ticket) பெறவும்!</em>""",

        'wizard': """ZeroGuard AI 5-படி புகார் பதிவு செய்யும் முறை:<br/><br/>
• <strong>படி 1 (சம்பவ விவரம்):</strong> தமிழ், ஆங்கிலம், இந்தி அல்லது தெலுங்கில் சம்பவத்தை எழுதுங்கள்.<br/>
• <strong>படி 2 (கேள்விகள்):</strong> மோசடி தொடர்பான கேள்விகளுக்கு பதிலளிக்கவும் (UTR, போன் எண்).<br/>
• <strong>படி 3 (பாதுகாப்பு வழிகாட்டி):</strong> அவசர பாதுகாப்பு முறைகள் மற்றும் ஆதாரங்களை இணைக்கவும்.<br/>
• <strong>படி 4 (முன்னோட்டம்):</strong> புகார் விவரங்களை சரிபார்க்கவும்.<br/>
• <strong>படி 5 (PDF பதிவிறக்கம்):</strong> காவல்துறைக்கான அதிகாரப்பூர்வ PDF புகார் அறிக்கையைப் பதிவிறக்கவும்.""",

        'anydesk': """போலி வாடிக்கையாளர் சேவை மற்றும் செயலிகள் எச்சரிக்கை:<br/><br/>
1. <strong>இணையத்தை முடக்கி செயலியை நீக்கவும்:</strong> உடனடியாக Wi-Fi/Mobile Data வை ஆஃப் செய்து AnyDesk, TeamViewer செயலிகளை நீக்கவும்.<br/>
2. <strong>வங்கி சேவையை முடக்கவும்:</strong> திரையைப் பகிர்வதன் மூலம் OTP திருடப்படலாம். உங்கள் வங்கியழைத்து நெட்பேங்கிங்கை முடக்கவும்.<br/>
3. <strong>எச்சரிக்கை:</strong> உண்மையான வங்கி ஊழியர்கள் ஒருபோதும் செயலிகளை பதிவிறக்கம் செய்ய சொல்ல மாட்டார்கள்!""",

        'telegram': """பகுதி நேர வேலை மற்றும் டெலிகிராம் பணி மோசடி:<br/><br/>
• <strong>செயல்முறை:</strong> யூடியூப் வீடியோக்களை லைக் செய்ய ₹150-500 தருவதாகக் கூறி, பின்னர் ₹10,000+ முதலீடு செய்யச் சொல்லி பணத்தை முடக்கி விடுவார்கள்.<br/>
• <strong>பாதுகாப்பு:</strong> இனிமேல் பணம் செலுத்த வேண்டாம். ஆதாரங்களுடன் 1930 அல்லது நமது தளத்தில் உடனடியாகப் புகார் அளிக்கவும்."""
    },
    'te': {
        'helpline': """ఆర్థిక సైబర్ నేరాల నుండి రక్షణ పొందడానికి తక్షణ చర్య తీసుకోండి:<br/><br/>
<strong>జాతీయ సైబర్ నేర అత్యవసర హెల్ప్‌లైన్ 1930:</strong><br/>
• <strong>ఇది ఏమి చేస్తుంది:</strong> పౌరులను నేరుగా నేషనల్ సైబర్ క్రైమ్ రిపోర్టింగ్ సిస్టమ్ (CFCFRMS)కి అనుసంధానిస్తుంది.<br/>
• <strong>గోల్డెన్ అవర్ (మొదటి 2-3 గంటలు):</strong> మోసం జరిగిన 2-3 గంటలలోపు 1930కి కాల్ చేస్తే, అధికారులు దొంగిలించబడిన నిధులను వెంటనే ఫ్రీజ్ చేయగలరు.<br/>
• <strong>సిద్ధంగా ఉంచుకోవాల్సినవి:</strong> మీ బ్యాంక్ ఖాతా సంఖ్య, డెబిట్ కార్డ్ చివరి 4 అంకెలు, అనుమానిత UPI ID మరియు UTR సంఖ్య.""",
        
        'upi': """UPI మరియు QR కోడ్ మోసాల కోసం తక్షణ రక్షణ చర్యలు:<br/><br/>
1. <strong>పాయింట్లు లేదా నగదు పొందడానికి UPI PIN నమోదు చేయవద్దు:</strong> UPI PIN కేవలం డబ్బు పంపడానికి మాత్రమే అవసరం, డబ్బు లేదా రీఫండ్ పొందడానికి ఎప్పుడూ కాదు.<br/>
2. <strong>వెంటనే 1930కి కాల్ చేయండి:</strong> 12-అంకెల UTR/RRN సంఖ్యను నివేదించండి.<br/>
3. <strong>యాప్‌లో ఫిర్యాదు చేయండి:</strong> GPay/PhonePe/Paytm లలో ట్రాన్సాక్షన్ హిస్టరీకి వెళ్లి ఫిర్యాదు నమోదు చేయండి.<br/>
4. <strong>UPI PIN మార్చండి:</strong> భద్రత కోసం మీ అన్ని బ్యాంక్ ఖాతాల UPI PIN ని వెంటనే రీసెట్ చేయండి.""",

        'sextort': """సెక్స్‌టార్షన్ మరియు ఆన్‌లైన్ బ్లాక్‌మెయిల్ కోసం అత్యవసర సూచనలు:<br/><br/>
<strong>దయచేసి భయపడవద్దు, డబ్బు పంపవద్దు:</strong><br/>
1. <strong>డబ్బు పంపవద్దు:</strong> బ్లాక్‌మెయిలర్‌కు డబ్బు చెల్లించడం వల్ల వీడియో డిలీట్ చేయబడదు, అది మరిన్ని డబ్బు డిమాండ్ చేయడానికి దారితీస్తుంది.<br/>
2. <strong>చాట్‌లను డిలీట్ చేయవద్దు:</strong> బెదిరింపు మెసేజ్‌లు, ఫోన్ నంబర్, UPI QR స్క్రీన్‌షాట్‌లను భద్రపరచండి.<br/>
3. <strong>సోషల్ మీడియా ప్రొఫైల్ లాక్ చేయండి:</strong> ఇన్స్టాగ్రామ్, ఫేస్‌బుక్ ప్రొఫైల్‌లను వెంటనే ప్రైవేట్‌గా మార్చండి.<br/>
4. <strong>StopNCII.org ఉపయోగించండి:</strong> ఈ టూల్ మీ ఫోటోలు ఆన్‌లైన్‌లో అప్‌లోడ్ కాకుండా నిరోధిస్తుంది.<br/>
5. <strong>చట్టపరమైన రక్షణ:</strong> IT చట్టం సెక్షన్ 67A కింద ఇది తీవ్రమైన నేరం. మా 5-స్టెప్ విజార్డ్ ద్వారా వెంటనే ఫిర్యాదు చేయండి.""",

        'rbi': """రిజర్వ్ బ్యాంక్ (RBI) జీరో కస్టమర్ లయబిలిటీ విధానం:<br/><br/>
• <strong>3 పని దినాలలోపు:</strong> మీ తప్పు లేకుండా జరిగిన అనధికార లావాదేవీని 3 రోజులలోపు బ్యాంక్‌కు నివేదిస్తే, మీకు <strong>జీరో లయబిలిటీ (Zero Liability)</strong> వర్తిస్తుంది, బ్యాంక్ పూర్తి మొత్తాన్ని రీఫండ్ చేస్తుంది.<br/>
• <strong>4 నుండి 7 రోజులలోపు:</strong> కస్టమర్ గరిష్ట బాధ్యత ₹10,000 వరకు మాత్రమే.<br/>
<em>ఎల్లప్పుడూ మీ బ్యాంక్ బ్రాంచ్ నుండి అధికారిక రసీదును (Acknowledgement Ticket) పొందండి!</em>""",

        'wizard': """ZeroGuard AI 5-స్టెప్ ఫిర్యాదు నమోదు విధానం:<br/><br/>
• <strong>స్టెప్ 1 (సంఘటన వివరాలు):</strong> తెలుగు, ఇంగ్లీష్, హిందీ లేదా తమిళంలో వివరాలు రాయండి.<br/>
• <strong>స్టెప్ 2 (ప్రశ్నలు):</strong> మోసానికి సంబంధించిన ప్రశ్నలకు సమాధానాలు ఇవ్వండి.<br/>
• <strong>స్టెప్ 3 (భద్రతా సూచనలు & ఆధారాలు):</strong> అత్యవసర భద్రతా సూచనలు చూడండి మరియు ఆధారాల స్క్రీన్‌షాట్‌లు జత చేయండి.<br/>
• <strong>స్టెప్ 4 (పరిశీలన):</strong> ఫిర్యాదు వివరాలను సరిచూసుకోండి.<br/>
• <strong>స్టెప్ 5 (PDF డౌన్‌లోడ్):</strong> పోలీసులకు సమర్పించగల అధికారిక PDF ఫిర్యాదు నివేదికను డౌన్‌లోడ్ చేయండి.""",

        'anydesk': """ఫేక్ కస్టమర్ కేర్ మరియు రిమోట్ యాప్‌ల హెచ్చరిక:<br/><br/>
1. <strong>ఇంటర్నెట్ నిలిపివేసి యాప్ అన్‌ఇన్‌స్టాల్ చేయండి:</strong> వెంటనే Wi-Fi/Mobile Data ఆఫ్ చేసి AnyDesk, TeamViewer యాప్‌లను డిలీట్ చేయండి.<br/>
2. <strong>బ్యాంకింగ్ సేవల నిలిపివేత:</strong> స్క్రీన్ షేరింగ్ ద్వారా OTP దొంగిలించబడవచ్చు. మీ బ్యాంక్‌కు కాల్ చేసి నెట్ బ్యాంకింగ్ ఫ్రీజ్ చేయండి.<br/>
3. <strong>హెచ్చరిక:</strong> నిజమైన బ్యాంక్ సిబ్బంది ఎప్పుడూ రిమోట్ యాప్‌లను డౌన్‌లోడ్ చేయమని కోరరు!""",

        'telegram': """పార్ట్-టైమ్ జాబ్ మరియు టెలిగ్రామ్ టాస్క్ స్కామ్:<br/><br/>
• <strong>పద్ధతి:</strong> యూట్యూబ్ వీడియోలను లైక్ చేయడానికి ₹150-500 ఇస్తామని ఎరవేసి, తర్వాత ₹10,000+ పెట్టుబడి పెట్టమని కోరి డబ్బును బ్లాక్ చేస్తారు.<br/>
• <strong>భద్రతా చర్య:</strong> ఇకపై ఎలాంటి డబ్బు చెల్లించవద్దు. ఆధారాలతో 1930కి లేదా మా పోర్టల్‌లో వెంటనే ఫిర్యాదు చేయండి."""
    }
}

# Detailed English rule-based knowledge fallback responses with empathetic tone
TOPIC_KNOWLEDGE_FALLBACK = [
    {
        'key': 'helpline',
        'patterns': [r'\b1930\b', r'helpline', r'golden hour', r'emergency number'],
        'response': """I understand this can be alarming — if you've suffered a financial loss, please stay calm and act right away.<br/><br/>
<strong>National Cybercrime Emergency Helpline 1930:</strong><br/>
• <strong>What it does:</strong> Connects citizens directly to the Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS).<br/>
• <strong>The Golden Hour (First 2-3 Hours):</strong> If you report unauthorized financial fraud within 2-3 hours of occurrence, nodal officers can immediately flag and freeze the stolen funds before the fraudster withdraws them at an ATM or transfers to mule accounts.<br/>
• <strong>What to have ready:</strong> Your bank account number, debit card last 4 digits, suspect UPI ID/account, and transaction SMS with UTR reference number."""
    },
    {
        'key': 'upi',
        'patterns': [r'upi', r'gpay', r'phonepe', r'paytm', r'qr code', r'cashback'],
        'response': """I'm sorry you're dealing with a suspicious transaction — let's help you protect your money and account immediately.<br/><br/>
<strong>Immediate Steps for UPI & QR Code Fraud:</strong><br/>
1. <strong>Do NOT enter PIN for receiving money:</strong> UPI PIN is ONLY required to send/transfer money, NEVER to receive cashback or refunds.<br/>
2. <strong>Call 1930 Immediately:</strong> Report the 12-digit UTR/RRN number.<br/>
3. <strong>Raise Dispute in App:</strong> Open GPay/PhonePe/Paytm &rarr; Transaction History &rarr; "Have an issue with this transaction" &rarr; Raise fraud dispute.<br/>
4. <strong>Change UPI PIN:</strong> Reset your UPI PIN across all bank accounts immediately to prevent unauthorized collect requests."""
    },
    {
        'key': 'sextort',
        'patterns': [r'sextort', r'nude', r'video call', r'blackmail', r'morph', r'intimate'],
        'response': """I am so sorry you are facing this distressful situation — please remember you are not alone, and do not panic or send money.<br/><br/>
<strong>Urgent Guidance for Sextortion & Blackmail:</strong><br/>
1. <strong>DO NOT SEND MONEY:</strong> Paying extortionists will NEVER make them delete the video; it only invites higher extortion demands.<br/>
2. <strong>Do NOT delete chats immediately:</strong> Take uncropped screenshots of threatening chats, the fraudster's phone number, UPI QR, and profile handles.<br/>
3. <strong>Lock your Social Profiles:</strong> Make your Instagram, Facebook, and LinkedIn private. Restrict direct messages.<br/>
4. <strong>Use StopNCII.org:</strong> StopNCII generates a non-reversible cryptographic hash of intimate media to block upload across Facebook, Instagram, TikTok, and OnlyFans.<br/>
5. <strong>Legal Protection:</strong> This is an offense under Section 67A (IT Act) & Section 384 (IPC/BNS Extortion). File a complaint through our 5-Step Wizard."""
    },
    {
        'key': 'rbi',
        'patterns': [r'rbi', r'zero liability', r'bank dispute', r'refund from bank', r'time limit'],
        'response': """Dealing with unauthorized bank transactions can be overwhelming — here is what you need to know about your rights under RBI rules.<br/><br/>
<strong>RBI Zero Liability Policy (Circular DBR.No.Leg.BC.78/09.07.005/2017-18):</strong><br/>
• <strong>Within 3 Working Days:</strong> If unauthorized transaction occurs due to third-party breach and you notify your bank within 3 working days, you have <strong>ZERO customer liability</strong>.<br/>
• <strong>Between 4 to 7 Working Days:</strong> Customer liability is capped at maximum Rs 10,000 (for savings accounts) or Rs 25,000 (for credit cards with limit > Rs 5 lakh).<br/>
• <strong>After 7 Days:</strong> As per bank's board-approved policy.<br/>
<em>Always obtain a formal dispute acknowledgment ticket from your bank branch!</em>"""
    },
    {
        'key': 'wizard',
        'patterns': [r'step 1', r'step 2', r'step 3', r'step 4', r'step 5', r'how to file', r'wizard'],
        'response': """I'm glad to assist you — here is a clear guide on how our 5-Step Guided Wizard builds your complaint report.<br/><br/>
<strong>ZeroGuard AI 5-Step Complaint Filing Process:</strong><br/>
• <strong>Step 1 (Incident Narrative):</strong> Type your incident in English, Hindi, Tamil, or Telugu. Our AI provides live risk triage and polishes your text.<br/>
• <strong>Step 2 (Follow-up Questions):</strong> Answer dynamic crime-specific questions (UTR, suspect handles, amounts).<br/>
• <strong>Step 3 (Safety Guidance & Evidence):</strong> Review immediate containment checklist and attach optional screenshots.<br/>
• <strong>Step 4 (Preview):</strong> Review the PII-scrubbed complaint summary.<br/>
• <strong>Step 5 (Submission & PDF):</strong> Generates an official ReportLab PDF complaint with reference code (<code>CC-YYYY-NNNNN</code>). Evidence files are auto-purged from the server for privacy."""
    },
    {
        'key': 'anydesk',
        'patterns': [r'anydesk', r'teamviewer', r'rustdesk', r'quicksupport', r'customer care scam'],
        'response': """If someone asked you to install a remote access app, please pause immediately — this is a high-risk tactic.<br/><br/>
<strong>Fake Customer Care & Remote App Alert:</strong><br/>
1. <strong>Disconnect Internet & Uninstall:</strong> Disconnect Wi-Fi/mobile data and uninstall AnyDesk / TeamViewer / RustDesk immediately.<br/>
2. <strong>Check Banking:</strong> Fraudsters use screen sharing to view your OTPs and netbanking passwords. Call your bank immediately to block netbanking.<br/>
3. <strong>Official Helplines:</strong> Real customer care teams never ask you to download remote access apps to process refunds!"""
    },
    {
        'key': 'telegram',
        'patterns': [r'telegram', r'job scam', r'part time job', r'youtube like', r'rating task'],
        'response': """Task and job scams can be very deceptive — I'm here to help you stop any further losses.<br/><br/>
<strong>Part-Time Job / Telegram Task Scam:</strong><br/>
• <strong>Modus Operandi:</strong> Fraudsters offer Rs 150-500 for liking YouTube videos or writing Google reviews. They pay small initial amounts to build trust, then demand Rs 10,000+ for "prepaid VIP tasks" and lock withdrawals.<br/>
• <strong>Action:</strong> Stop making any deposits. Export Telegram chat logs and suspect UPI handles, and register a complaint to help Cyber-Cells freeze the beneficiary accounts."""
    }
]

def detect_script_language(text: str) -> str:
    """
    Detects language based on Unicode script ranges in user's typed input:
    - Devanagari script (Hindi): U+0900–U+097F
    - Tamil script: U+0B80–U+0BFF
    - Telugu script: U+0C00–U+0C7F
    Returns 'hi', 'ta', 'te', or None if no non-Latin Indian script is found.
    """
    if not text:
        return None

    hi_count = len(re.findall(r'[\u0900-\u097F]', text))
    ta_count = len(re.findall(r'[\u0B80-\u0BFF]', text))
    te_count = len(re.findall(r'[\u0C00-\u0C7F]', text))

    counts = {'hi': hi_count, 'ta': ta_count, 'te': te_count}
    max_lang = max(counts, key=counts.get)

    if counts[max_lang] > 0:
        return max_lang

    return None


@chatbot_bp.route('/chatbot')
def chatbot_page():
    """Renders the full-page AI cyber assistant interface."""
    return render_template('chatbot/chatbot.html')

@chatbot_bp.route('/api/chat', methods=['POST'])
@csrf.exempt
def api_chat():
    """Handles multi-turn conversational AI queries with automatic Unicode script language detection."""
    data = request.get_json() or {}
    user_msg = data.get('message', '').strip()
    history = data.get('history', [])
    is_manual_override = data.get('is_manual_override', False)
    explicit_lang = (data.get('language') or data.get('response_language') or '').lower().strip()

    if not user_msg:
        return jsonify({'error': 'Empty message'}), 400

    clean_msg = redact_pii(user_msg)

    # 1. Automatic Unicode Script Language Auto-Detection from typed message text
    script_lang = detect_script_language(clean_msg)

    # 2. Priority Resolution:
    #    - Script auto-detection from typed text ALWAYS takes top priority if non-Latin script is present.
    #    - If user manually selected a language override in dropdown (is_manual_override == True), honor explicit_lang.
    #    - Otherwise (plain English text without manual dropdown override), switch back to English ('en') automatically!
    if script_lang:
        language = script_lang
    elif is_manual_override and explicit_lang in SUGGESTIONS_BY_LANG:
        language = explicit_lang
    else:
        language = 'en'

    # Store resolved language in session
    session['chat_language'] = language
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    # Try Gemini Multi-Turn Generation with Language Instruction
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Format history (keep last 8 turns)
            recent_history = history[-8:]
            formatted_history = "\n".join([f"{h.get('role', 'user').title()}: {h.get('text', '')}" for h in recent_history])
            
            # Multi-language instruction prompt injection
            lang_instructions = {
                'hi': "\nCRITICAL RESPONSE LANGUAGE: Reply entirely in Hindi (हिंदी) script. Use polite, reassuring, clear Devanagari Hindi.",
                'ta': "\nCRITICAL RESPONSE LANGUAGE: Reply entirely in Tamil (தமிழ்) script. Use polite, reassuring, clear Tamil language.",
                'te': "\nCRITICAL RESPONSE LANGUAGE: Reply entirely in Telugu (తెలుగు) script. Use polite, reassuring, clear Telugu language.",
                'en': "\nCRITICAL RESPONSE LANGUAGE: Reply in clear, polite English."
            }
            
            lang_prompt_str = lang_instructions.get(language, lang_instructions['en'])
            system_context = CHATBOT_SYSTEM_PROMPT.format(history=formatted_history if formatted_history else 'New conversation started.') + lang_prompt_str
            full_prompt = f"{system_context}\n\nUser: {clean_msg}\nAI Assistant:"
            
            response = model.generate_content(full_prompt)
            reply_text = response.text.strip()
            
            # Quick classification
            rule_eval = classify_by_rules(clean_msg)
            
            return jsonify({
                'response': reply_text.replace('\n', '<br/>'),
                'crime_type': rule_eval['crime_type'],
                'risk_level': rule_eval['risk_level'],
                'suggestions': SUGGESTIONS_BY_LANG.get(language, SUGGESTIONS_BY_LANG['en']),
                'detected_language': language,
                'source': f'Gemini AI ({language.upper()})'
            })
        except Exception as e:
            current_app.logger.error(f"[GEMINI API ERROR] Chatbot failed to query Gemini API: {e}", exc_info=True)
            print(f"[GEMINI API ERROR] Chatbot Gemini call failed: {e}", flush=True)

    # Fallback to topic knowledge engine (with translations)
    msg_lower = clean_msg.lower()
    for topic in TOPIC_KNOWLEDGE_FALLBACK:
        for pattern in topic['patterns']:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                rule_eval = classify_by_rules(clean_msg)
                
                # Fetch translated response if available
                resp_text = topic['response']
                topic_key = topic.get('key')
                if language != 'en' and topic_key in TOPIC_KNOWLEDGE_TRANSLATIONS.get(language, {}):
                    resp_text = TOPIC_KNOWLEDGE_TRANSLATIONS[language][topic_key]
                
                return jsonify({
                    'response': resp_text,
                    'crime_type': rule_eval['crime_type'],
                    'risk_level': rule_eval['risk_level'],
                    'suggestions': SUGGESTIONS_BY_LANG.get(language, SUGGESTIONS_BY_LANG['en']),
                    'detected_language': language,
                    'source': f'Rule-Based Knowledge Hub ({language.upper()})'
                })

    rule_eval = classify_by_rules(clean_msg)
    
    # Generic fallback in target language
    generic_resp = f"I understand you have a question regarding <strong>{rule_eval['crime_type']}</strong>. Here is what you should do:<br/><br/>" \
                   f"1. Preserve all electronic records, transaction IDs, and communication screenshots without tampering.<br/>" \
                   f"2. If financial loss occurred within the last 2-3 hours, dial <strong>1930</strong> immediately.<br/>" \
                   f"3. You can compile an official complaint letter via our 5-Step Guided Wizard."
                   
    if language == 'hi':
        generic_resp = f"मैं समझता हूँ कि आपका प्रश्न <strong>{rule_eval['crime_type']}</strong> से संबंधित है। कृपया इन चरणों का पालन करें:<br/><br/>" \
                       f"1. सभी इलेक्ट्रॉनिक रिकॉर्ड, लेनदेन आईडी और स्क्रीनशॉट सुरक्षित रखें।<br/>" \
                       f"2. यदि वित्तीय धोखाधड़ी हाल ही में हुई है, तो तुरंत <strong>1930</strong> पर कॉल करें।<br/>" \
                       f"3. आप हमारे 5-स्टेप विजार्ड से पुलिस शिकायत रिपोर्ट तैयार कर सकते हैं।"
    elif language == 'ta':
        generic_resp = f"உங்கள் கேள்வி <strong>{rule_eval['crime_type']}</strong> பற்றியது என்பதைப் புரிந்து கொள்கிறேன். பின்வரும் நடவடிக்கைகளை எடுக்கவும்:<br/><br/>" \
                       f"1. அனைத்து ஆன்லைன் ஆதாரங்கள், UTR எண்கள் மற்றும் சாட்களின் ஸ்கிரீன்ஷாட்களைப் பாதுகாக்கவும்.<br/>" \
                       f"2. பண இழப்பு ஏற்பட்டால் உடனடியாக <strong>1930</strong> என்ற எண்ணை அழைக்கவும்.<br/>" \
                       f"3. நமது 5-படி வழிகாட்டியைப் பயன்படுத்தி அதிகாரப்பூர்வ புகார் அறிக்கையை உருவாக்கலாம்."
    elif language == 'te':
        generic_resp = f"మీ ప్రశ్న <strong>{rule_eval['crime_type']}</strong> కి సంబంధించినదని నేను అర్థం చేసుకున్నాను. దయచేసి ఈ క్రింది చర్యలు తీసుకోండి:<br/><br/>" \
                       f"1. అన్ని ఆన్‌లైన్ ఆధారాలు, UTR నంబర్‌లు మరియు స్క్రీన్‌షాట్‌లను భద్రపరచండి.<br/>" \
                       f"2. ఆర్థిక నష్టం జరిగినట్లయితే వెంటనే <strong>1930</strong> కి కాల్ చేయండి.<br/>" \
                       f"3. మా 5-స్టెప్ విజార్డ్ ద్వారా మీరు అధికారిక ఫిర్యాదు నివేదికను తయారు చేయవచ్చు."

    return jsonify({
        'response': generic_resp,
        'crime_type': rule_eval['crime_type'],
        'risk_level': rule_eval['risk_level'],
        'suggestions': SUGGESTIONS_BY_LANG.get(language, SUGGESTIONS_BY_LANG['en']),
        'detected_language': language,
        'source': f'Rule-Based Knowledge Hub ({language.upper()})'
    })
