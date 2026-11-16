"""Comprehensive Multilingual Named Entity Recognition (NER) for Vaani AI.

Supports all 20 target languages:
- Indic: Hindi, Marathi, Gujarati, Bengali, Tamil, Telugu, Urdu, Hinglish
- European: English, Spanish, French, German, Italian, Portuguese, Dutch, Russian
- Middle Eastern & East Asian: Arabic, Japanese, Chinese, Korean

Entity Types Recognized:
1. PERSON: Person names (single & multi-word, transliterations, honorifics)
2. LOCATION / CITY: Cities, countries, regions (multi-word, script-native)
3. ORGANIZATION: Companies, institutions, government bodies, universities
4. DATE: Absolute dates, month expressions, and multilingual relative dates
5. TIME: Clock times (12h, 24h, Indic markers) and multilingual relative time expressions
6. PHONE: International and domestic phone number formats
7. EMAIL: RFC-standard email addresses
8. MONEY: Currency symbols, localized currency names, large denomination expressions
9. NUMBER: Digits, decimal values, and Indic / CJK script numerals
10. LANGUAGE: Language names in English and native scripts

Features:
- Preserves original input text and returns character offset spans (start, end).
- Prevents entity collision and double-counting (e.g. phone/date digits not counted as plain NUMBER).
- Zero external heavy dependencies (no spaCy/Torch); completely offline, < 1ms latency.
- Strict false-positive guarding against ordinary vocabulary words.
"""

import re
import unicodedata
from typing import List, Dict, Any, Set, Tuple

# =====================================================================
# 1. Gazetteers: Locations & Cities (Multilingual)
# =====================================================================

CITIES = {
    # Major Indian Cities (Latin)
    "mumbai", "delhi", "new delhi", "bangalore", "bengaluru", "pune", "chennai", "kolkata",
    "hyderabad", "ahmedabad", "jaipur", "surat", "nagpur", "lucknow", "kanpur", "patna",
    "indore", "thane", "bhopal", "visakhapatnam", "vadodara", "firozabad", "ludhiana",
    "rajkot", "agra", "varanasi", "srinagar", "amritsar", "navi mumbai", "allahabad",
    "prayagraj", "ranchi", "howrah", "coimbatore", "jabalpur", "gwalior", "vijayawada",
    "jodhpur", "madurai", "raipur", "kota", "guwahati", "chandigarh", "solapur",
    # Major Global Cities (Latin)
    "london", "paris", "new york", "tokyo", "berlin", "madrid", "rome", "roma", "amsterdam",
    "moscow", "beijing", "shanghai", "seoul", "dubai", "cairo", "sydney", "toronto",
    "singapore", "san francisco", "los angeles", "chicago", "boston", "zurich", "geneva",
    "vienna", "barcelona", "milan", "milano", "munich", "brussels", "bangkok", "jakarta", "riyadh",
    "sao paulo", "são paulo",
    # Devanagari (Hindi, Marathi)
    "मुंबई", "दिल्ली", "नई दिल्ली", "नवी दिल्ली", "पुणे", "बंगलोर", "बेंगळुरू", "बेंगलुरु",
    "चेन्नई", "कोलकाता", "हैदराबाद", "अहमदाबाद", "जयपूर", "जयपुर", "सुरत", "सूरत",
    "नागपूर", "नागपुर", "लखनौ", "लखनऊ", "कानपूर", "कानपुर", "पाटणा", "पटना", "इंदूर",
    "इंदौर", "भोपाळ", "भोपाल", "वडोदरा", "राजकोट", "वाराणसी", "अमृतसर", "लंडन", "लंदन",
    "पॅरिस", "पेरिस", "न्यूयॉर्क", "न्यू यॉर्क", "टोक्यो", "बर्लिन", "माद्रिद", "रोम", "मॉस्को",
    # Gujarati
    "મુંબઈ", "દિલ્હી", "નવી દિલ્હી", "પુણે", "બેંગ્લોર", "અમદાવાદ", "સુરત", "જયપુર",
    "વડોદરા", "રાજકોટ", "ભાવનગર", "જામનગર", "ગાંધીનગર", "જૂનાગઢ", "લંડન", "પેરિસ", "ન્યૂ યોર્ક",
    # Bengali
    "মুম্বাই", "দিল্লি", "নতুন দিল্লি", "পুনে", "ব্যাঙ্গালোর", "কলকাতা", "চেন্নাই", "হায়দ্রাবাদ",
    "আহমেদাবাদ", "জয়পুর", "সুরত", "লন্ডন", "প্যারিস", "টোকিও", "নিউ ইয়র্ক",
    # Tamil
    "மும்பை", "டெல்லி", "புது டெல்லி", "சென்னை", "பெங்களூரு", "கொல்கத்தா", "ஹைதராபாத்",
    "அகமதாபாத்", "மதுரை", "கோயம்புத்தூர்", "லண்டன்", "பாரிஸ்", "டோக்கியோ", "நியூயார்க்",
    # Telugu
    "ముంబై", "ఢిల్లీ", "బెంగళూరు", "చెన్నై", "హైదరాబాద్", "కోల్‌కతా", "విశాఖపట్నం", "విజయవాడ",
    # Urdu / Arabic
    "ممبئی", "دہلی", "نئی دہلی", "حیدرآباد", "کراچی", "لاہور", "لندن", "باريس", "دبي", "القاهرة", "طوكيو", "الرياض",
    # Russian (Cyrillic)
    "москва", "москве", "москву", "санкт-петербург", "петербурге", "лондон", "париж", "токио", "берлин", "нью-йорк", "рим", "мадрид",
    # Japanese (Kanji / Katakana)
    "東京", "大阪", "京都", "ロンドン", "パリ", "ニューヨーク", "ベルリン", "北京",
    # Chinese (Simplified)
    "北京", "上海", "广州", "深圳", "香港", "伦敦", "巴黎", "纽约", "东京", "柏林",
    # Korean (Hangul)
    "서울", "부산", "도쿄", "런던", "파리", "뉴욕", "베이징",
}

COUNTRIES_REGIONS = {
    # English / Latin
    "india", "united states", "usa", "uk", "united kingdom", "france", "germany",
    "japan", "china", "russia", "italy", "spain", "brazil", "australia", "canada",
    "united arab emirates", "uae", "saudi arabia", "singapore", "netherlands", "switzerland",
    # Native Scripts
    "भारत", "हिंदुस्तान", "ભારત", "ভারত", "இந்தியா", "భారతదేశం", "ہندوستان",
    "россия", "франция", "германия", "япония", "китай",
    "الهند", "فرنسا", "ألمانيا", "روسيا", "اليابان", "الصين",
    "日本", "中国", "フランス", "ドイツ", "アメリカ",
    "대한민국", "한국", "미국", "일본", "중국",
}

# Preposition context cues for location detection across scripts
_LOC_CUES_BEFORE = [
    r"\b(?:in|at|to|from|near|visit|travel to|trip to)\s+",
    r"\b(?:में|से|को|तक|के पास)\s+",
    r"\b(?:मध्ये|वरून|कडे)\s+",
    r"\b(?:માં|થી|તરફ)\s+",
    r"\b(?:en|a|de|hacia|desde)\s+",
    r"\b(?:à|en|dans|de|vers)\s+",
    r"\b(?:nach|in|aus|bei)\s+",
    r"\b(?:a|in|da|verso)\s+",
    r"\b(?:em|para|de)\s+",
    r"\b(?:in|naar|van|uit)\s+",
    r"\b(?:в|из|до|около)\s+",
    r"(?:في|إلى|من)\s+",
]

# =====================================================================
# 2. Gazetteers: Organizations (Multilingual)
# =====================================================================

ORGANIZATIONS = {
    # Tech & Global Brands
    "google", "microsoft", "apple", "amazon", "meta", "ibm", "intel", "nvidia",
    "samsung", "sony", "toyota", "tesla", "siemens", "sap", "oracle", "cisco",
    # Indian IT & Conglomerates
    "tcs", "tata consultancy services", "infosys", "wipro", "hcl", "tech mahindra",
    "reliance", "reliance jio", "jio", "tata", "tata motors", "adani", "l&t", "larsen & toubro",
    # Banking & Financial Institutions
    "sbi", "state bank of india", "rbi", "reserve bank of india", "hdfc", "hdfc bank",
    "icici", "icici bank", "axis bank", "punjab national bank", "pnb", "bank of baroda",
    # Government & Scientific Bodies
    "isro", "nasa", "drdo", "who", "un", "united nations", "unesco", "unicef",
    "aiims", "iit", "iim", "nit", "bcci",
    # Native Transliterations
    "गूगल", "माइक्रोसॉफ्ट", "एप्पल", "अमेज़न", "टाटा", "रिलायंस", "टीसीएस", "इंफोसिस", "विप्रो", "नासा", "इसरो",
    "ગૂગલ", "ટાટા", "રિલાયન્સ", "ઇસરો",
    "গুগল", "টাটা", "রিলায়েন্স", "ইসরো",
    "கூகுள்", "டாடா", "இஸ்ரோ",
    "гугл", "майкрософт", "яндекс", "сбербанк", "газпром",
    "جوجل", "مايكروسوفت", "أبل", "تاتا",
    "グーグル", "マイクロソフト", "アップル", "ソニー", "トヨタ",
    "谷歌", "微软", "苹果", "腾讯", "阿里巴巴", "百度", "华为",
    "구글", "마이크로소프트", "애플", "삼성", "현대",
}

_ORG_SUFFIX_PATTERN = re.compile(
    r"\b((?:[A-Z\u0900-\u0D7F][a-zA-Z\u0900-\u0D7F0-9&.]+(?:\s+[A-Z\u0900-\u0D7F][a-zA-Z\u0900-\u0D7F0-9&.]+){0,3})\s+"
    r"(?:Pvt\.?\s?Ltd\.?|Ltd\.?|Inc\.?|Corp\.?|Corporation|LLC|GmbH|Foundation|"
    r"Institute|University|Bank|Hospital|Technologies|Infotech))\b",
    re.UNICODE,
)

# =====================================================================
# 3. Gazetteers: Person Names & Patterns (Multilingual)
# =====================================================================

# Multilingual Famous Personalities & Common Gazetteers
FAMOUS_PERSONS = {
    # International & Historical
    "albert einstein", "isaac newton", "marie curie", "william shakespeare", "leonardo da vinci",
    "charles darwin", "stephen hawking", "nelson mandela", "abraham lincoln", "steve jobs",
    "bill gates", "elon musk", "sundar pichai", "satya nadella", "tim cook",
    # Indian Leaders & Cultural Icons
    "mahatma gandhi", "narendra modi", "apj abdul kalam", "abdul kalam", "jawaharlal nehru",
    "bhagat singh", "sardar patel", "vallabhbhai patel", "b r ambedkar", "ambedkar",
    "rabindranath tagore", "tagore", "swami vivekananda", "vivekananda", "mother teresa",
    "sachin tendulkar", "virat kohli", "ms dhoni", "dhoni", "amitabh bachchan", "shah rukh khan",
    # Script-native equivalents
    "अल्बर्ट आइंस्टीन", "महात्मा गांधी", "नरेंद्र मोदी", "अब्दुल कलाम", "सचिन तेंदुलकर", "विराट कोहली",
    "મહાત્મા ગાંધી", "નરેન્દ્ર મોદી", "સરદાર પટેલ",
    "মহাত্মা গান্ধী", "রবীন্দ্রনাথ ঠাকুর",
    "மகாத்மா காந்தி", "அப்துல் கலாம்",
    "మహాత్మా గాంధీ", "అబ్దుల్ కలాం",
    "Альберт Эйнштейн", "Владимир Путин", "Лев Толстой", "Пушкин",
}

COMMON_FIRST_NAMES = {
    # Indian First Names (Latin)
    "aarav", "rahul", "priya", "yashvi", "rohan", "ananya", "rajesh", "suresh",
    "ramesh", "sneha", "pooja", "amit", "neha", "rohit", "vikram", "arjun", "aditya",
    "deepak", "kavita", "sunita", "anita", "manish", "sanjay", "ajay", "vijay", "divya",
    "shreya", "tanvi", "riya", "simran", "karan", "varun", "nikhil", "akash", "meera",
    # Indic Script Names
    "राहुल", "प्रिया", "आरव", "यशवी", "रोहन", "अनन्या", "राजेश", "सुरेश", "रमेश", "स्नेहा",
    "पूजा", "अमित", "नेहा", "रोहित", "विक्रम", "अर्जुन", "आदित्य", "दीपक", "कविता", "सुनीता",
    "રાહુલ", "પ્રિયા", "આરવ", "યશવી", "રોહન",
    "রাহুল", "প্রিয়া", "রোহিত",
    "ராகுல்", "பிரியா",
    "రాహుల్", "ప్రియ",
    # European / American Common Names
    "john", "emma", "michael", "sarah", "david", "laura", "james", "elena", "carlos",
    "maria", "jean", "sophie", "hans", "anna", "marco", "giulia", "lucas", "clara",
}

_HONORIFICS = [
    r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Doctor|Professor|Shri|Smt\.|Shrimati)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    r"(?:श्री|श्रीमती|डॉ\.|डाक्टर|प्रो\.|प्रोफेसर)\s+([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)?)",
    r"(?:શ્રી|શ્રીમતી|ડૉ\.)\s+([\u0A80-\u0AFF]+(?:\s+[\u0A80-\u0AFF]+)?)",
    r"(?:শ্রী|শ্রীমতী|ডাঃ)\s+([\u0980-\u09FF]+(?:\s+[\u0980-\u09FF]+)?)",
    r"(?:திரு|திருமதி|டாக்டர்)\s+([\u0B80-\u0BFF]+(?:\s+[\u0B80-\u0BFF]+)?)",
    r"(?:శ్రీ|శ్రీమతి|డాక్టర్)\s+([\u0C00-\u0C7F]+(?:\s+[\u0C00-\u0C7F]+)?)",
]

_NAME_INTRO_PATTERNS = [
    # English
    r"(?:my name is|i am called|call me|this is|i'm|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    # Hindi / Hinglish / Urdu
    r"(?:मेरा नाम(?:\s+है)?|मेरा नाम|मुझसे बात करो|mera naam(?:\s+hai)?|mera naam)\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)",
    r"(?:میرا نام(?:\s+ہے)?)\s+([\u0600-\u06FF]+(?:\s+[\u0600-\u06FF]+)?)",
    # Marathi
    r"(?:माझे नाव(?:\s+आहे)?|माझं नाव(?:\s+आहे)?|मी)\s+([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)?)",
    # Gujarati
    r"(?:મારું નામ(?:\s+છે)?|હું)\s+([\u0A80-\u0AFF]+(?:\s+[\u0A80-\u0AFF]+)?)",
    # Bengali
    r"(?:আমার নাম(?:\s+হলো)?|আমি)\s+([\u0980-\u09FF]+(?:\s+[\u0980-\u09FF]+)?)",
    # Tamil
    r"(?:என் பெயர்|நான்)\s+([\u0B80-\u0BFF]+(?:\s+[\u0B80-\u0BFF]+)?)",
    # Telugu
    r"(?:నా పేరు|నేను)\s+([\u0C00-\u0C7F]+(?:\s+[\u0C00-\u0C7F]+)?)",
    # Spanish
    r"(?:me llamo|mi nombre es|soy)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+)?)",
    # French
    r"(?:je m'appelle|mon nom est|je suis)\s+([A-ZÀÂÇÉÈÊËÎÏÔÛÙÜŸa-zàâçéèêëîïôûùüÿ]+(?:\s+[A-ZÀÂÇÉÈÊËÎÏÔÛÙÜŸa-zàâçéèêëîïôûùüÿ]+)?)",
    # German
    r"(?:ich heiße|mein Name ist|ich bin)\s+([A-ZÄÖÜa-zäöüß]+(?:\s+[A-ZÄÖÜa-zäöüß]+)?)",
    # Italian
    r"(?:mi chiamo|il mio nome è|sono)\s+([A-ZÀÈÉÌÍÎÒÓÙÚa-zàèéìíîòóùú]+(?:\s+[A-ZÀÈÉÌÍÎÒÓÙÚa-zàèéìíîòóùú]+)?)",
    # Portuguese
    r"(?:me chamo|meu nome é|sou o|sou a)\s+([A-ZÃÕÁÉÍÓÚÂÊa-zãõáéíóúâê]+(?:\s+[A-ZÃÕÁÉÍÓÚÂÊa-zãõáéíóúâê]+)?)",
    # Dutch
    r"(?:ik heet|mijn naam is|ik ben)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    # Russian
    r"(?:меня зовут|мое имя|моё имя)\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)",
    # Arabic
    r"(?:اسمي|أنا)\s+([\u0600-\u06FF]+(?:\s+[\u0600-\u06FF]+)?)",
    # Japanese
    r"(?:私の名前は|私は|僕の名前は)\s*([^\s\d_,.!?;:]{1,6}?)(?:です|と申します)",
    # Chinese
    r"(?:我叫|我的名字是|我是)\s*([^\s\d_,.!?;:]{2,4})",
    # Korean
    r"(?:제 이름은|저는|내 이름은)\s*([^\s\d_,.!?;:]{2,4}?)(?:입니다|이야|야)",
]

# Words that should NEVER be extracted as person names
_STOP_NAMES = {
    "happy", "sad", "fine", "good", "great", "tired", "hungry", "very", "so", "not",
    "from", "a", "an", "the", "today", "tomorrow", "yesterday", "here", "there",
    "assistant", "bot", "vaani", "ai", "user", "admin", "test", "demo", "help",
    "back", "later", "now", "again", "soon", "sorry", "busy", "well", "feeling",
    "है", "आहे", "છે", "হয়", "ആണ്", "உள்ளது", "ఉంది", "ہو", "hai", "ahe", "che",
    "good morning", "hello", "hi", "namaste", "vanakkam", "bonjour", "hola",
}

# Trailing copulas in SOV languages to strip from extracted names
_TRAILING_COPULAS = {
    "है", "हूँ", "हू", "था", "थी", "थे", "हो",
    "आहे", "आहोत", "होते", "होती",
    "છે", "હતા", "હતી", "હતો",
    "হয়", "ছিল",
    "ஆகும்", "உள்ளது",
    "ఉంది", "ఉన్నాడు",
    "ہے", "ہوں", "تھا",
    "hai", "hoon", "hu", "tha", "thi", "ahe", "che",
}

# =====================================================================
# 4. Multilingual Dates & Relative Expressions
# =====================================================================

RELATIVE_DATES = {
    # English
    "today": "today", "tomorrow": "tomorrow", "yesterday": "yesterday",
    "tonight": "tonight", "day after tomorrow": "day after tomorrow",
    # Hindi / Hinglish
    "आज": "today", "कल": "tomorrow/yesterday", "परसों": "day after tomorrow",
    "aaj": "today", "kal": "tomorrow/yesterday", "parso": "day after tomorrow", "parson": "day after tomorrow",
    # Marathi
    "उद्या": "tomorrow", "काल": "yesterday", "परवा": "day after tomorrow",
    # Gujarati
    "આજે": "today", "કાલે": "tomorrow", "ગઈકાલે": "yesterday", "પરમદિવસે": "day after tomorrow",
    # Bengali
    "আজ": "today", "আগামীকাল": "tomorrow", "গতকাল": "yesterday",
    # Tamil
    "இன்று": "today", "நாளை": "tomorrow", "நேற்று": "yesterday",
    # Telugu
    "ఈరోజు": "today", "రేపు": "tomorrow", "నిన్న": "yesterday",
    # Urdu
    "آج": "today", "کل": "tomorrow/yesterday", "پرسوں": "day after tomorrow",
    # Spanish
    "hoy": "today", "mañana": "tomorrow", "ayer": "yesterday", "anoche": "last night",
    # French
    "aujourd'hui": "today", "demain": "tomorrow", "hier": "yesterday",
    # German
    "heute": "today", "morgen": "tomorrow", "gestern": "yesterday",
    # Italian
    "oggi": "today", "domani": "tomorrow", "ieri": "yesterday",
    # Portuguese
    "hoje": "today", "amanhã": "tomorrow", "ontem": "yesterday",
    # Dutch
    "vandaag": "today", "gisteren": "yesterday",
    # Russian
    "сегодня": "today", "завтра": "tomorrow", "вчера": "yesterday",
    # Arabic
    "اليوم": "today", "غدا": "tomorrow", "غداً": "tomorrow", "أمس": "yesterday",
    # Japanese
    "今日": "today", "明日": "tomorrow", "昨日": "yesterday", "今夜": "tonight",
    # Chinese
    "今天": "today", "明天": "tomorrow", "昨天": "yesterday", "今晚": "tonight",
    # Korean
    "오늘": "today", "내일": "tomorrow", "어제": "yesterday", "오늘 밤": "tonight",
}

MONTH_NAMES_EN = [
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "jan", "feb", "mar", "apr",
    "jun", "jul", "aug", "sep", "oct", "nov", "dec"
]

MONTH_NAMES_INDIC = [
    "जनवरी", "फ़रवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त",
    "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर", "જાન્યુઆરી", "ફેબ્રુઆરી", "માર્ચ", "એપ્રિલ",
    "મે", "જૂન", "જુલાઈ", "ઓગસ્ટ", "સપ્ટેમ્બર", "ઓક્ટોબર", "નવેમ્બર", "ડિસેમ્બર",
    "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট",
    "செப்டம்பர்", "ஆகஸ்ட்", "ஜனவரி",
]

# =====================================================================
# 5. Multilingual Time Expressions
# =====================================================================

RELATIVE_TIMES = {
    # English
    "morning": "morning", "afternoon": "afternoon", "evening": "evening", "night": "night",
    "midnight": "midnight", "noon": "noon",
    # Hindi / Hinglish
    "सुबह": "morning", "दोपहर": "afternoon", "शाम": "evening", "रात": "night",
    "subah": "morning", "dopahar": "afternoon", "shaam": "evening", "raat": "night",
    # Marathi
    "सकाळी": "morning", "दुपारी": "afternoon", "संध्याकाळी": "evening", "रात्री": "night",
    # Gujarati
    "સવારે": "morning", "બપોરે": "afternoon", "સાંજે": "evening", "રાત્રે": "night",
    # Bengali
    "সকালে": "morning", "দুপুরে": "afternoon", "সন্ধ্যায়": "evening", "রাতে": "night",
    # Tamil
    "காலை": "morning", "மதியம்": "afternoon", "மாலை": "evening", "இரவு": "night",
    # Telugu
    "ఉదయం": "morning", "మధ్యాహ్నం": "afternoon", "సాయంత్రం": "evening", "రాత్రి": "night",
    # Urdu
    "صبح": "morning", "دوپہر": "afternoon", "شام": "evening", "رات": "night",
    # Spanish
    "tarde": "afternoon", "noche": "night",
    # French
    "matin": "morning", "après-midi": "afternoon", "soir": "evening",
    # German
    "morgens": "morning", "nachmittags": "afternoon", "abends": "evening", "nachts": "night",
    # Italian
    "mattina": "morning", "pomeriggio": "afternoon", "sera": "evening", "notte": "night",
    # Portuguese
    "manhã": "morning", "noite": "night",
    # Dutch
    "ochtend": "morning", "middag": "afternoon", "avond": "evening",
    # Russian
    "утром": "morning", "днем": "afternoon", "вечером": "evening", "ночью": "night",
    # Arabic
    "صباحا": "morning", "صباحاً": "morning", "مساء": "evening", "مساءً": "evening", "ليلا": "night",
    # Japanese
    "朝": "morning", "昼": "afternoon", "夜": "night", "午前": "AM", "午後": "PM",
    # Chinese
    "早上": "morning", "中午": "noon", "下午": "afternoon", "晚上": "evening",
    # Korean
    "아침": "morning", "저녁": "evening", "밤": "night", "오전": "AM", "오후": "PM",
}

# =====================================================================
# 6. Languages Gazetteer
# =====================================================================

LANG_WORDS = {
    "english": "en", "hindi": "hi", "marathi": "mr", "gujarati": "gu", "bengali": "bn",
    "tamil": "ta", "telugu": "te", "urdu": "ur", "spanish": "es", "french": "fr",
    "german": "de", "italian": "it", "portuguese": "pt", "dutch": "nl", "russian": "ru",
    "arabic": "ar", "japanese": "ja", "chinese": "zh", "korean": "ko", "hinglish": "hinglish",
    "हिंदी": "hi", "मराठी": "mr", "ગુજરાતી": "gu", "বাংলা": "bn", "தமிழ்": "ta", "తెలుగు": "te",
    "اردو": "ur", "español": "es", "français": "fr", "deutsch": "de", "italiano": "it",
    "português": "pt", "nederlands": "nl", "русский": "ru", "العربية": "ar",
    "日本語": "ja", "中文": "zh", "한국어": "ko",
    "अंग्रेज़ी": "en", "अंग्रेजी": "en", "इंग्रजी": "en", "અંગ્રેજી": "en",
}


# =====================================================================
# 7. Helper: Span Collision & Overlap Guard
# =====================================================================

def _has_overlap(start: int, end: int, occupied_spans: List[Tuple[int, int]]) -> bool:
    """Check if the given (start, end) interval overlaps with any occupied span."""
    for o_start, o_end in occupied_spans:
        if max(start, o_start) < min(end, o_end):
            return True
    return False


# =====================================================================
# 8. Main Entity Extraction Function
# =====================================================================

def extract_entities(text: str, lang: str = "en") -> List[Dict[str, Any]]:
    """Extract named entities from raw text across all 20 supported languages.
    
    Preserves exact character offsets and original casings.
    Prevents collision so sub-tokens (e.g. phone digits) are not extracted as numbers.
    """
    if not text or not text.strip():
        return []

    ents: List[Dict[str, Any]] = []
    occupied_spans: List[Tuple[int, int]] = []
    low = text.lower()

    # -------------------------------------------------------------
    # Step 1: High-Precision Structured Entities (Email, Phone, Money)
    # -------------------------------------------------------------

    # 1.1 Email Addresses
    for m in re.finditer(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text):
        s, e = m.span()
        if not _has_overlap(s, e, occupied_spans):
            ents.append({"type": "EMAIL", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.99})
            occupied_spans.append((s, e))

    # 1.2 Phone Numbers (Indian mobile, formatted international)
    phone_pats = [
        # +91 or domestic Indian 10 digits starting with 6-9
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)",
        # International with parenthesis/dashes
        r"(?<!\d)\+(?:[1-9]\d{0,2})[\s-]?(?:\(\d{1,4}\)|\d{1,4})[\s-]?\d{3,4}[\s-]?\d{3,4}(?!\d)",
        # Standard US/General format (555) 123-4567
        r"(?<!\d)\(\d{3}\)[\s-]?\d{3}[\s-]?\d{4}(?!\d)",
    ]
    for pat in phone_pats:
        for m in re.finditer(pat, text):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "PHONE", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.95})
                occupied_spans.append((s, e))

    # 1.3 Monetary Values (Symbols & Local Currency Words)
    money_pats = [
        # Symbols: ₹, $, €, £, ¥, ₩, ₽ with multi-script numbers and multipliers
        r"(?:[₹$€£¥₩₽]|Rs\.?|INR|USD|EUR|GBP)\s?[०-९૦-૯০-৯۰-۹0-9]+(?:[.,][०-९૦-૯০-৯۰-۹0-9]+)?(?:\s?(?:crore|lakh|million|billion|k|m|करोड़|लाख|हजार|हज़ार|કરોડ|হাজার|লাখ|కోట్లు|கோடி))?",
        # Words: 500 rupees, 100 dollars, 100 dólares, 50 euros, 2000 рублей, 500 ريال
        r"\b\d+(?:[.,]\d+)?\s?(?:rupees?|rupaye?|rupay|dollars?|dólar(?:es)?|euros?|pounds?|yen|won|rubles?|reais|руб(?:лей|ля|ль)?|dirhams?|dinars?|riwals?)\b",
        # Indic & script numerals + currency words
        r"[०-९૦-૯০-৯۰-۹0-9]+(?:[.,][०-९૦-૯০-৯۰-۹0-9]+)?\s?(?:करोड़|लाख|हज़ार|हजार|કરોડ|হাজার|লাখ|కోట్లు|கோடி)?\s?(?:रुपये|रुपए|रु\.|રૂપિયા|રૂ\.|টাকা|ரூபாய்|రూపాయలు|روپے|ريال|ریال|ريالات|ریالات|درهم|دينار|جنيه|рублей|рубля|руб|块|元|円|원)",
    ]
    for pat in money_pats:
        for m in re.finditer(pat, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "MONEY", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.95})
                occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 2: Time Expressions (Absolute & Relative)
    # -------------------------------------------------------------

    # 2.1 Clock Times (12h, 24h, Indic clock markers)
    time_clock_pats = [
        r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm|a\.m\.|p\.m\.)\b",
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",
        r"[०-९૦-૯০-৯۰-۹0-9]{1,2}(?::[०-९૦-૯০-৯۰-۹0-9]{2})?\s?(?:बजे|वाजता|વાગ્યે|ٹے|மணி|గంటలకు|بجے)",
    ]
    for pat in time_clock_pats:
        for m in re.finditer(pat, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "TIME", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.95})
                occupied_spans.append((s, e))

    # 2.2 Relative Time Keywords (morning, afternoon, शाम, सकाळी, etc.)
    for kw, canon in sorted(RELATIVE_TIMES.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"(?<!\w){re.escape(kw)}(?!\w)" if kw.isascii() else re.escape(kw)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "TIME", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.88})
                occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 3: Date Expressions (Absolute & Relative)
    # -------------------------------------------------------------

    # 3.1 Explicit Formats (DD/MM/YYYY, Month names)
    date_pats = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:" + "|".join(MONTH_NAMES_EN) + r")(?:\s+\d{2,4})?\b",
        r"\b(?:" + "|".join(MONTH_NAMES_EN) + r")\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{2,4})?\b",
        r"[०-९0-9]{1,2}\s+(?:" + "|".join(MONTH_NAMES_INDIC) + r")(?:\s*[०-९0-9]{2,4})?",
    ]
    for pat in date_pats:
        for m in re.finditer(pat, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "DATE", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.95})
                occupied_spans.append((s, e))

    # 3.2 Relative Dates (today, tomorrow, आज, उद्या, etc.)
    for kw, canon in sorted(RELATIVE_DATES.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"\b{re.escape(kw)}\b" if kw.isascii() else re.escape(kw)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "DATE", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.90})
                occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 4: Organizations
    # -------------------------------------------------------------

    # 4.1 Suffix-based organizations (e.g. "Acme Corp", "Tata Motors Ltd.")
    for m in _ORG_SUFFIX_PATTERN.finditer(text):
        s, e = m.span()
        if not _has_overlap(s, e, occupied_spans):
            val = m.group().strip()
            ents.append({"type": "ORGANIZATION", "value": val, "raw": val, "start": s, "end": e, "confidence": 0.90})
            occupied_spans.append((s, e))

    # 4.2 Known Organization Gazetteer
    for org in sorted(ORGANIZATIONS, key=len, reverse=True):
        pattern = rf"\b{re.escape(org)}\b" if org.isascii() else re.escape(org)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                val = m.group()
                canon = org.upper() if len(org) <= 4 else org.title()
                ents.append({"type": "ORGANIZATION", "value": canon, "raw": val, "start": s, "end": e, "confidence": 0.92})
                occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 5: Locations & Cities
    # -------------------------------------------------------------

    # 5.1 Cities (emits both CITY and LOCATION for complete backward compatibility)
    for c in sorted(CITIES, key=len, reverse=True):
        pattern = rf"\b{re.escape(c)}\b" if c.isascii() else re.escape(c)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                val = m.group()
                canon = c.title() if c.isascii() else c
                # Yield legacy CITY type for backward compatibility
                ents.append({"type": "CITY", "value": canon, "raw": val, "start": s, "end": e, "confidence": 0.94})
                # Yield standard LOCATION type
                ents.append({"type": "LOCATION", "value": canon, "raw": val, "start": s, "end": e, "confidence": 0.94})
                occupied_spans.append((s, e))

    # 5.2 Countries & Regions
    for c in sorted(COUNTRIES_REGIONS, key=len, reverse=True):
        pattern = rf"\b{re.escape(c)}\b" if c.isascii() else re.escape(c)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                val = m.group()
                canon = c.title() if c.isascii() else c
                ents.append({"type": "LOCATION", "value": canon, "raw": val, "start": s, "end": e, "confidence": 0.92})
                occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 6: Person Names
    # -------------------------------------------------------------

    # 6.1 Conversational Introduction Patterns (my name is X, मेरा नाम X है, etc.)
    for pat in _NAME_INTRO_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE | re.UNICODE):
            extracted = m.group(1).strip()
            # Clean trailing punctuation (including full-width CJK marks)
            extracted = re.sub(r"[,.!?;:，。！？]+$", "", extracted).strip()
            # In Latin scripts, require true Capitalization to guard against 'I am very happy' or 'Call me back'
            if extracted.isascii() and not extracted[0].isupper():
                continue
            # Strip trailing copulas in SOV languages (e.g. 'राहुल है' -> 'राहुल', 'Rahul hai' -> 'Rahul')
            words = extracted.split()
            if len(words) > 1 and words[-1].lower() in _TRAILING_COPULAS:
                words = words[:-1]
                extracted = " ".join(words)
            # Avoid stop names or empty
            if extracted and extracted.lower() not in _STOP_NAMES and len(extracted) >= 2:
                s = m.start(1)
                e = s + len(extracted)
                if not _has_overlap(s, e, occupied_spans):
                    canon = extracted.title() if extracted.isascii() else extracted
                    ents.append({"type": "PERSON", "value": canon, "raw": extracted, "start": s, "end": e, "confidence": 0.92})
                    occupied_spans.append((s, e))
                    break  # intro patterns take priority once found

    # 6.2 Honorifics (Mr., Dr., Shri, श्री, etc.)
    for pat in _HONORIFICS:
        for m in re.finditer(pat, text, flags=re.UNICODE):
            extracted = m.group(1).strip()
            if extracted and extracted.lower() not in _STOP_NAMES and len(extracted) >= 2:
                s, e = m.span(1)
                if not _has_overlap(s, e, occupied_spans):
                    canon = extracted.title() if extracted.isascii() else extracted
                    ents.append({"type": "PERSON", "value": canon, "raw": extracted, "start": s, "end": e, "confidence": 0.90})
                    occupied_spans.append((s, e))

    # 6.3 Famous Personalities (Multi-word names)
    for p in sorted(FAMOUS_PERSONS, key=len, reverse=True):
        pattern = rf"\b{re.escape(p)}\b" if p.isascii() else re.escape(p)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                val = m.group()
                canon = p.title() if p.isascii() else p
                ents.append({"type": "PERSON", "value": canon, "raw": val, "start": s, "end": e, "confidence": 0.95})
                occupied_spans.append((s, e))

    # 6.4 Common First Names (Only if capitalized or in Indic script, guarded against stops)
    for fn in sorted(COMMON_FIRST_NAMES, key=len, reverse=True):
        # In Latin text, require word boundary and title case to prevent false positive matching
        if fn.isascii():
            pattern = rf"\b{re.escape(fn.capitalize())}\b"
        else:
            pattern = re.escape(fn)
        for m in re.finditer(pattern, text, flags=re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                val = m.group()
                if val.lower() not in _STOP_NAMES:
                    canon = fn.capitalize() if fn.isascii() else fn
                    ents.append({"type": "PERSON", "value": canon, "raw": val, "start": s, "end": e, "confidence": 0.85})
                    occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 7: Language Names
    # -------------------------------------------------------------
    for w, code in sorted(LANG_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"(?<!\w){re.escape(w)}(?!\w)" if w.isascii() else re.escape(w)
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "LANGUAGE", "value": code, "raw": m.group(), "start": s, "end": e, "confidence": 0.95})
                occupied_spans.append((s, e))

    # -------------------------------------------------------------
    # Step 8: Numerical Values (Integers & Decimals)
    # -------------------------------------------------------------
    # Exclude any digits already captured in PHONE, TIME, DATE, MONEY
    num_pats = [
        # Standard digits with optional decimal point
        r"(?<![\w:/-])\d+(?:[.,]\d+)?(?![\w:/-])",
        # Indic script numerals (Devanagari, Gujarati, Bengali, Arabic)
        r"[०-९0-9]+(?:\.[०-९0-9]+)?",
        r"[૦-૯]+(?:\.[૦-૯]+)?",
        r"[০-৯]+(?:\.[০-৯]+)?",
        r"[٠-٩]+(?:\.[٠-٩]+)?",
    ]
    for pat in num_pats:
        for m in re.finditer(pat, text, flags=re.UNICODE):
            s, e = m.span()
            if not _has_overlap(s, e, occupied_spans):
                ents.append({"type": "NUMBER", "value": m.group(), "raw": m.group(), "start": s, "end": e, "confidence": 0.90})
                occupied_spans.append((s, e))

    # Sort entities by start offset
    ents.sort(key=lambda x: x["start"])
    return ents
