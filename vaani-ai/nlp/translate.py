"""Machine translation with automatic fallback.

Engine order:
  1. Google Translate via `deep-translator` (needs internet).
  2. Offline phrasebook (small curated dictionary) so the demo keeps working without internet.
"""
import re
from .languages import HINGLISH, LANGUAGES

# Small offline phrasebook: English phrase -> {lang: translation}. Keys are lower-case, no punctuation.
PHRASEBOOK = {
    "hello": {"hi": "नमस्ते", "mr": "नमस्कार", "gu": "નમસ્તે", "bn": "নমস্কার", "ta": "வணக்கம்", "es": "hola", "fr": "bonjour", "de": "hallo"},
    "good morning": {"hi": "सुप्रभात", "mr": "शुभ प्रभात", "gu": "સુપ્રભાત", "bn": "সুপ্রভাত", "ta": "காலை வணக்கம்", "es": "buenos días", "fr": "bonjour", "de": "guten Morgen"},
    "good night": {"hi": "शुभ रात्रि", "mr": "शुभ रात्री", "gu": "શુભ રાત્રિ", "bn": "শুভ রাত্রি", "ta": "இனிய இரவு", "es": "buenas noches", "fr": "bonne nuit", "de": "gute Nacht"},
    "thank you": {"hi": "धन्यवाद", "mr": "धन्यवाद", "gu": "આભાર", "bn": "ধন্যবাদ", "ta": "நன்றி", "es": "gracias", "fr": "merci", "de": "danke"},
    "how are you": {"hi": "आप कैसे हैं", "mr": "तुम्ही कसे आहात", "gu": "તમે કેમ છો", "bn": "আপনি কেমন আছেন", "ta": "நீங்கள் எப்படி இருக்கிறீர்கள்", "es": "¿cómo estás?", "fr": "comment allez-vous", "de": "wie geht es dir"},
    "goodbye": {"hi": "अलविदा", "mr": "निरोप", "gu": "આવજો", "bn": "বিদায়", "ta": "போய் வருகிறேன்", "es": "adiós", "fr": "au revoir", "de": "auf Wiedersehen"},
    "welcome": {"hi": "स्वागत है", "mr": "स्वागत आहे", "gu": "સ્વાગત છે", "bn": "স্বাগতম", "ta": "வரவேற்கிறோம்", "es": "bienvenido", "fr": "bienvenue", "de": "willkommen"},
    "what is your name": {"hi": "आपका नाम क्या है", "mr": "तुमचे नाव काय आहे", "gu": "તમારું નામ શું છે", "bn": "আপনার নাম কী", "ta": "உங்கள் பெயர் என்ன", "es": "¿cómo te llamas?", "fr": "comment vous appelez-vous", "de": "wie heißt du"},
    "i love you": {"hi": "मैं तुमसे प्यार करता हूँ", "es": "te quiero", "fr": "je t'aime", "de": "ich liebe dich"},
    "please help me": {"hi": "कृपया मेरी मदद करें", "es": "por favor ayúdame", "fr": "aidez-moi s'il vous plaît", "de": "bitte hilf mir"},
    "water": {"hi": "पानी", "mr": "पाणी", "gu": "પાણી", "bn": "জল", "ta": "தண்ணீர்", "es": "agua", "fr": "eau", "de": "Wasser"},
    "i am happy": {"hi": "मैं खुश हूँ", "es": "estoy feliz", "fr": "je suis heureux", "de": "ich bin glücklich"},
    "i am sad": {"hi": "मैं उदास हूँ", "es": "estoy triste", "fr": "je suis triste", "de": "ich bin traurig"},
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
    src = "hi" if src == HINGLISH else src
    if src == tgt:
        return {"text": text, "engine": "identity", "ok": True}

    try:
        from deep_translator import GoogleTranslator
        out = GoogleTranslator(source="auto" if src not in LANGUAGES else src, target=tgt).translate(text)
        if out:
            return {"text": out, "engine": "google (online)", "ok": True}
    except Exception:
        pass  # no internet / rate-limited -> offline fallback

    out = _offline(text, src, tgt)
    if out:
        return {"text": out, "engine": "offline phrasebook", "ok": True}
    return {"text": text, "engine": "unavailable", "ok": False}
