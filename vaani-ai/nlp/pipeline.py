"""End-to-end pipeline used by the API: text -> preprocess -> language -> sentiment -> intent/NER -> reply."""
from datetime import datetime
from zoneinfo import ZoneInfo

from .chatbot import Chatbot
from .languages import LANGUAGES, name_of, reply_lang
from .langid import detect_language
from .preprocess import preprocess
from .sentiment import analyze
from .translate import translate

_bot = None


def get_bot() -> Chatbot:
    global _bot
    if _bot is None:
        _bot = Chatbot()
    return _bot


def _now(tz):
    try:
        return datetime.now(ZoneInfo(tz)) if tz else datetime.now()
    except Exception:
        return datetime.now()


def process(text: str, reply_to="auto", translate_to="en", tz=None) -> dict:
    text = (text or "").strip()
    if not text:
        return {"error": "Empty input"}
    det = detect_language(text)
    code = det["code"]
    lang_for_prep = "hi" if code == "hinglish" else code
    prep = preprocess(text, lang_for_prep)
    sent = analyze(text, lang_for_prep)
    target = reply_lang(code) if reply_to == "auto" else reply_to
    chat = get_bot().respond(text, code, target, now=_now(tz), sentiment=sent)
    tr = translate(text, code, translate_to)
    return {
        "input": text,
        "language": {**det, "name": name_of(code)},
        "preprocessing": prep,
        "sentiment": sent,
        "intent": {"name": chat["intent"], "confidence": chat["confidence"], "ranked": chat["ranked"]},
        "entities": chat["entities"],
        "translation": {**tr, "target": translate_to, "target_name": name_of(translate_to)},
        "reply": {"text": chat["reply"], "english": chat["reply_en"], "lang": chat["reply_lang"],
                  "tts": LANGUAGES.get(chat["reply_lang"], LANGUAGES["en"])["tts"], "engine": chat["engine"]},
    }
