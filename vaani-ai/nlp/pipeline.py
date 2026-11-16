"""End-to-end pipeline used by the API: text -> preprocess -> language -> sentiment -> intent/NER -> reply."""
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv

# Automatically load environment variables from .env
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

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


def process(text: str, reply_to="auto", translate_to="en", tz=None, session_id=None) -> dict:
    t_start = time.perf_counter()
    text = (text or "").strip()
    if not text:
        return {"error": "Empty input"}

    t_nlp_start = time.perf_counter()
    det = detect_language(text)
    code = det["code"]
    prep = preprocess(text, code)
    sent = analyze(text, "hi" if code == "hinglish" else code)
    local_nlp_ms = round((time.perf_counter() - t_nlp_start) * 1000.0, 2)

    target = reply_lang(code) if reply_to == "auto" else reply_to
    chat = get_bot().respond(text, code, target, now=_now(tz), sentiment=sent, session_id=session_id)
    tr = translate(text, code, translate_to)
    total_pipeline_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "input": text,
        "session_id": chat.get("session_id"),
        "language": {**det, "name": name_of(code)},
        "preprocessing": prep,
        "sentiment": sent,
        "intent": {"name": chat["intent"], "confidence": chat["confidence"], "ranked": chat.get("ranked", [])},
        "entities": chat["entities"],
        "translation": {**tr, "target": translate_to, "target_name": name_of(translate_to)},
        "timing": {
            "local_nlp_ms": local_nlp_ms,
            "chatbot_ms": chat.get("latency_ms", 0.0),
            "total_ms": total_pipeline_ms,
        },
        "reply": {
            "text": chat["reply"],
            "english": chat["reply_en"],
            "lang": chat["reply_lang"],
            "tts": LANGUAGES.get(chat["reply_lang"], LANGUAGES["en"])["tts"],
            "engine": chat["engine"],
            "model": chat.get("model"),
            "latency_ms": chat.get("latency_ms"),
        },
    }
