"""Machine translation with automatic multi-tier fallback.

Engine order:
  1. Offline phrasebook (curated dictionary) for instant, human-verified translations.
  2. Google Translate via `deep-translator` (fastest, high accuracy).
  3. MyMemory Translator via `deep-translator` (reliable online fallback on Google rate limits).
  4. Identity/unavailable graceful fallback.
"""
import re
from .languages import HINGLISH, LANGUAGES

# Curated offline phrasebook: English phrase -> {lang: translation}. Keys are lower-case, no punctuation.
PHRASEBOOK = {
    "hello": {
        "hi": "नमस्ते", "mr": "नमस्कार", "gu": "નમસ્તે", "bn": "নমস্কার", "ta": "வணக்கம்",
        "es": "hola", "fr": "bonjour", "de": "hallo", "nl": "hallo", "it": "ciao",
        "pt": "olá", "ru": "здравствуйте", "ar": "مرحباً", "ja": "こんにちは", "zh": "你好",
        "ko": "안녕하세요", "te": "నమస్కారం", "ur": "ہیلو",
    },
    "good morning": {
        "hi": "सुप्रभात", "mr": "शुभ प्रभात", "gu": "સુપ્રભાત", "bn": "সুপ্রভাত", "ta": "காலை வணக்கம்",
        "es": "buenos días", "fr": "bonjour", "de": "guten Morgen", "nl": "goedemorgen", "it": "buongiorno",
        "pt": "bom dia", "ru": "доброе утро", "ar": "صباح الخير", "ja": "おはようございます", "zh": "早上好",
        "ko": "좋은 아침입니다", "te": "శుభోదయం", "ur": "صبح بخیر",
    },
    "good afternoon": {
        "hi": "शुभ दोपहर", "mr": "शुभ दुपार", "gu": "શુભ બપોર", "bn": "শুভ অপরাহ্ন", "ta": "மதிய வணக்கம்",
        "es": "buenas tardes", "fr": "bon après-midi", "de": "guten Tag", "nl": "goedemiddag", "it": "buon pomeriggio",
        "pt": "boa tarde", "ru": "добрый день", "ar": "مساء الخير", "ja": "こんにちは", "zh": "下午好",
        "ko": "좋은 오후입니다", "te": "శుభ మధ్యాహ్నం", "ur": "دوپہر بخیر",
    },
    "good evening": {
        "hi": "शुभ संध्या", "mr": "शुभ संध्याकाळ", "gu": "શુભ સાંજ", "bn": "শুভ সন্ধ্যা", "ta": "மாலை வணக்கம்",
        "es": "buenas tardes", "fr": "bonsoir", "de": "guten Abend", "nl": "goedenavond", "it": "buonasera",
        "pt": "boa noite", "ru": "добрый вечер", "ar": "مساء الخير", "ja": "こんばんは", "zh": "晚上好",
        "ko": "좋은 저녁입니다", "te": "శుభ సాయంత్రం", "ur": "شام بخیر",
    },
    "good night": {
        "hi": "शुभ रात्रि", "mr": "शुभ रात्री", "gu": "શુભ રાત્રિ", "bn": "শুভ রাত্রি", "ta": "இனிய இரவு",
        "es": "buenas noches", "fr": "bonne nuit", "de": "gute Nacht", "nl": "goedenacht", "it": "buonanotte",
        "pt": "boa noite", "ru": "спокойной ночи", "ar": "تصبح على خير", "ja": "おやすみなさい", "zh": "晚安",
        "ko": "안녕히 주무세요", "te": "శుభ రాత్రి", "ur": "شب بخیر",
    },
    "thank you": {
        "hi": "धन्यवाद", "mr": "धन्यवाद", "gu": "આભાર", "bn": "ধন্যবাদ", "ta": "நன்றி",
        "es": "gracias", "fr": "merci", "de": "danke", "nl": "dank je wel", "it": "grazie",
        "pt": "obrigado", "ru": "спасибо", "ar": "شكراً لك", "ja": "ありがとうございます", "zh": "谢谢",
        "ko": "감사합니다", "te": "ధన్యవాదాలు", "ur": "شکریہ",
    },
    "how are you": {
        "hi": "आप कैसे हैं", "mr": "तुम्ही कसे आहात", "gu": "તમે કેમ છો", "bn": "আপনি কেমন আছেন", "ta": "நீங்கள் எப்படி இருக்கிறீர்கள்",
        "es": "¿cómo estás?", "fr": "comment allez-vous", "de": "wie geht es dir", "nl": "hoe gaat het", "it": "come stai",
        "pt": "como vai", "ru": "как дела", "ar": "كيف حالك", "ja": "お元気ですか", "zh": "你好吗",
        "ko": "어떻게 지내세요", "te": "మీరు ఎలా ఉన్నారు", "ur": "آپ کیسے ہیں",
    },
    "goodbye": {
        "hi": "अलविदा", "mr": "निरोप", "gu": "આવજો", "bn": "বিদায়", "ta": "போய் வருகிறேன்",
        "es": "adiós", "fr": "au revoir", "de": "auf Wiedersehen", "nl": "tot ziens", "it": "arrivederci",
        "pt": "tchau", "ru": "до свидания", "ar": "مع السلامة", "ja": "さようなら", "zh": "再见",
        "ko": "안녕히 가세요", "te": "వీడ్కోలు", "ur": "الوداع",
    },
    "welcome": {
        "hi": "स्वागत है", "mr": "स्वागत आहे", "gu": "સ્વાગત છે", "bn": "স্বাগতম", "ta": "வரவேற்கிறோம்",
        "es": "bienvenido", "fr": "bienvenue", "de": "willkommen", "nl": "welkom", "it": "benvenuto",
    },
    "what is your name": {
        "hi": "आपका नाम क्या है", "mr": "तुमचे नाव काय आहे", "gu": "તમારું નામ શું છે", "bn": "আপনার নাম কী", "ta": "உங்கள் பெயர் என்ன",
        "es": "¿cómo te llamas?", "fr": "comment vous appelez-vous", "de": "wie heißt du", "nl": "hoe heet je", "it": "come ti chiami",
        "ru": "как вас зовут", "ar": "ما اسمك", "ja": "お名前は何ですか", "zh": "你叫什么名字", "ko": "이름이 무엇입니까",
    },
    "i'm eating": {
        "hi": "मैं खा रहा हूँ", "mr": "मी खात आहे", "gu": "હું ખાઈ રહ્યો છું", "ta": "நான் சாப்பிடுகிறேன்", "bn": "আমি খাচ্ছি",
        "es": "estoy comiendo", "fr": "je mange", "de": "ich esse", "nl": "ik ben aan het eten", "it": "sto mangiando",
    },
    "i am eating": {
        "hi": "मैं खा रहा हूँ", "mr": "मी खात आहे", "gu": "હું ખાઈ રહ્યો છું", "ta": "நான் சாப்பிடுகிறேன்", "bn": "আমি খাচ্ছি",
        "es": "estoy comiendo", "fr": "je mange", "de": "ich esse", "nl": "ik ben aan het eten", "it": "sto mangiando",
    },
}

MYMEMORY_LOCALE_MAP = {
    "en": "en-US", "hi": "hi-IN", "mr": "mr-IN", "gu": "gu-IN", "bn": "bn-IN",
    "ta": "ta-IN", "te": "te-IN", "ur": "ur-PK", "es": "es-ES", "fr": "fr-FR",
    "de": "de-DE", "it": "it-IT", "pt": "pt-PT", "nl": "nl-NL", "ru": "ru-RU",
    "ar": "ar-SA", "ja": "ja-JP", "zh": "zh-CN", "ko": "ko-KR",
}

# Reverse index: foreign phrase -> (english, {lang: text})
_REVERSE = {}
for _en, _tr in PHRASEBOOK.items():
    for _lg, _txt in _tr.items():
        _REVERSE[_txt.lower().strip(" ?!.,।")] = _en


def _key(text: str) -> str:
    from .preprocess import normalize
    return re.sub(r"[?!.,।]", "", normalize(text).lower()).strip()


def _offline(text: str, src: str, tgt: str):
    k = _key(text)
    english = k if k in PHRASEBOOK else _REVERSE.get(k)
    if english is None:
        return None
    if tgt == "en":
        return english
    return PHRASEBOOK[english].get(tgt)


def translate(text: str, src: str, tgt: str) -> dict:
    """Translate `text` from src to tgt. Returns {text, engine, ok}."""
    text = (text or "").strip()
    if not text:
        return {"text": "", "engine": "none", "ok": True}

    # Resolve 'auto' source using fast script detection or English default
    if src == "auto" or not src:
        from .langid import detect_language
        det = detect_language(text)
        src = det.get("code", "en") if det.get("confidence", 0) >= 0.6 else "en"

    src = "hi" if src == HINGLISH else src
    tgt = "hi" if tgt == HINGLISH else tgt
    if src == tgt:
        return {"text": text, "engine": "identity", "ok": True}

    # Tier 1: Check curated phrasebook first for instant, accurate verified translations
    out = _offline(text, src, tgt)
    if out:
        return {"text": out, "engine": "offline phrasebook", "ok": True}

    # Tier 2: Google Translator via deep_translator (for arbitrary text)
    try:
        from deep_translator import GoogleTranslator
        out = GoogleTranslator(source="auto" if src not in LANGUAGES else src, target=tgt).translate(text)
        if out and out.strip():
            return {"text": out.strip(), "engine": "google (online)", "ok": True}
    except Exception:
        pass  # Rate limited or offline -> continue to Tier 3

    # Tier 3: MyMemory Translator via deep_translator
    try:
        from deep_translator import MyMemoryTranslator
        src_locale = MYMEMORY_LOCALE_MAP.get(src, src)
        tgt_locale = MYMEMORY_LOCALE_MAP.get(tgt, tgt)
        out = MyMemoryTranslator(source=src_locale, target=tgt_locale).translate(text)
        if out and out.strip() and not out.startswith("MYMEMORY WARNING"):
            return {"text": out.strip(), "engine": "mymemory (online)", "ok": True}
    except Exception:
        pass

    return {"text": text, "engine": "unavailable", "ok": False}
