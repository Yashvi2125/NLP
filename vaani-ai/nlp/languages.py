"""Supported languages and metadata shared by all modules."""

LANGUAGES = {
    "en": {"name": "English", "speech": "en-IN", "tts": "en-IN"},
    "hi": {"name": "Hindi", "speech": "hi-IN", "tts": "hi-IN"},
    "mr": {"name": "Marathi", "speech": "mr-IN", "tts": "mr-IN"},
    "gu": {"name": "Gujarati", "speech": "gu-IN", "tts": "gu-IN"},
    "bn": {"name": "Bengali", "speech": "bn-IN", "tts": "bn-IN"},
    "ta": {"name": "Tamil", "speech": "ta-IN", "tts": "ta-IN"},
    "es": {"name": "Spanish", "speech": "es-ES", "tts": "es-ES"},
    "fr": {"name": "French", "speech": "fr-FR", "tts": "fr-FR"},
    "de": {"name": "German", "speech": "de-DE", "tts": "de-DE"},
}
# "hinglish" = Hindi written in Latin script; treated as Hindi for replies.
HINGLISH = "hinglish"


def name_of(code: str) -> str:
    if code == HINGLISH:
        return "Hinglish (Hindi in Roman script)"
    return LANGUAGES.get(code, {}).get("name", code)


def reply_lang(code: str) -> str:
    """Language the assistant should reply in for a detected language."""
    if code == HINGLISH:
        return "hi"
    return code if code in LANGUAGES else "en"
