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
        if tz:
            return datetime.now(ZoneInfo(tz))
        return datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        try:
            return datetime.now(ZoneInfo("Asia/Kolkata"))
        except Exception:
            return datetime.now()


def process(text: str, reply_to="auto", translate_to="en", tz=None, session_id=None, speech_lang=None) -> dict:
    t_start = time.perf_counter()
    text = (text or "").strip()
    if not text:
        return {"error": "Empty input"}

    t_nlp_start = time.perf_counter()
    # Respect explicit user "I speak" selection when provided
    user_override = False
    if speech_lang and speech_lang != "auto":
        cand = speech_lang.split("-")[0].lower()
        if cand in LANGUAGES:
            det = {
                "code": cand,
                "name": name_of(cand),
                "confidence": 1.0,
                "method": "user-selection:override",
                "is_mixed": False,
                "candidates": [[cand, 1.0]],
                "user_override": True,
            }
            user_override = True
        else:
            det = detect_language(text)
    else:
        det = detect_language(text)

    code = det["code"]
    prep = preprocess(text, code)
    sent = analyze(text, "hi" if code == "hinglish" else code)
    local_nlp_ms = round((time.perf_counter() - t_nlp_start) * 1000.0, 2)

    target = reply_lang(code) if reply_to == "auto" else reply_to
    chat = get_bot().respond(text, code, target, now=_now(tz), sentiment=sent, session_id=session_id)
    chatbot_ms = float(chat.get("latency_ms", 0.0))

    # Precedence Rules for Translation Target (A1 & A3):
    # 1. If translate_to is 'auto' (or omitted), sync directly with reply target.
    # 2. If translate_to matches the input language (e.g. input is English and translate_to is 'en'),
    #    falling through to identity is a no-op. If a foreign reply_to was selected, route to reply_to.
    # 3. Otherwise, use explicit translate_to selection.
    if translate_to in ("auto", None, ""):
        eff_trans_target = target if target != "auto" else ("hi" if code == "en" else "en")
    elif translate_to == code and target not in ("auto", code):
        eff_trans_target = target
    else:
        eff_trans_target = translate_to

    t_trans_start = time.perf_counter()
    tr = translate(text, code, eff_trans_target)
    translation_ms = round((time.perf_counter() - t_trans_start) * 1000.0, 2)

    total_pipeline_ms = round(local_nlp_ms + chatbot_ms + translation_ms, 2)

    return {
        "input": text,
        "session_id": chat.get("session_id"),
        "language": {**det, "name": name_of(code)},
        "preprocessing": prep,
        "sentiment": sent,
        "intent": {"name": chat["intent"], "confidence": chat["confidence"], "ranked": chat.get("ranked", [])},
        "entities": chat["entities"],
        "translation": {
            **tr,
            "target": eff_trans_target,
            "target_name": name_of(eff_trans_target),
            "latency_ms": translation_ms,
        },
        "timing": {
            "local_nlp_ms": local_nlp_ms,
            "chatbot_ms": chatbot_ms,
            "translation_ms": translation_ms,
            "total_ms": total_pipeline_ms,
        },
        "reply": {
            "text": chat["reply"],
            "english": chat["reply_en"],
            "reply_en": chat["reply_en"],
            "lang": chat["reply_lang"],
            "tts": chat.get("speak_tts") or LANGUAGES.get(chat["reply_lang"], LANGUAGES["en"])["tts"],
            "speak_text": chat.get("speak_text") or chat["reply"],
            "engine": chat["engine"],
            "model": chat.get("model"),
            "latency_ms": chatbot_ms,
        },
    }
