"""Supported languages, regional metadata, speech codes, and capability tiers for Vaani AI."""

LANGUAGES = {
    # Core Indian Regional Languages (Phase 1 & 2 trained)
    "en": {"name": "English", "native": "English", "speech": "en-IN", "tts": "en-IN", "tier": "core", "script": "latin"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "speech": "hi-IN", "tts": "hi-IN", "tier": "core", "script": "devanagari"},
    "mr": {"name": "Marathi", "native": "मराठी", "speech": "mr-IN", "tts": "mr-IN", "tier": "core", "script": "devanagari"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "speech": "gu-IN", "tts": "gu-IN", "tier": "core", "script": "gujarati"},
    "bn": {"name": "Bengali", "native": "বাংলা", "speech": "bn-IN", "tts": "bn-IN", "tier": "core", "script": "bengali"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "speech": "ta-IN", "tts": "ta-IN", "tier": "core", "script": "tamil"},
    "te": {"name": "Telugu", "native": "తెలుగు", "speech": "te-IN", "tts": "te-IN", "tier": "extended", "script": "telugu"},
    "ur": {"name": "Urdu", "native": "اردو", "speech": "ur-PK", "tts": "ur-PK", "tier": "extended", "script": "arabic"},

    # European Languages
    "es": {"name": "Spanish", "native": "Español", "speech": "es-ES", "tts": "es-ES", "tier": "international", "script": "latin"},
    "fr": {"name": "French", "native": "Français", "speech": "fr-FR", "tts": "fr-FR", "tier": "international", "script": "latin"},
    "de": {"name": "German", "native": "Deutsch", "speech": "de-DE", "tts": "de-DE", "tier": "international", "script": "latin"},
    "it": {"name": "Italian", "native": "Italiano", "speech": "it-IT", "tts": "it-IT", "tier": "international", "script": "latin"},
    "pt": {"name": "Portuguese", "native": "Português", "speech": "pt-BR", "tts": "pt-BR", "tier": "international", "script": "latin"},
    "nl": {"name": "Dutch", "native": "Nederlands", "speech": "nl-NL", "tts": "nl-NL", "tier": "international", "script": "latin"},
    "ru": {"name": "Russian", "native": "Русский", "speech": "ru-RU", "tts": "ru-RU", "tier": "international", "script": "cyrillic"},

    # Asian & Middle Eastern Languages
    "ar": {"name": "Arabic", "native": "العربية", "speech": "ar-SA", "tts": "ar-SA", "tier": "international", "script": "arabic"},
    "ja": {"name": "Japanese", "native": "日本語", "speech": "ja-JP", "tts": "ja-JP", "tier": "international", "script": "japanese"},
    "zh": {"name": "Chinese (Simplified)", "native": "简体中文", "speech": "zh-CN", "tts": "zh-CN", "tier": "international", "script": "chinese"},
    "ko": {"name": "Korean", "native": "한국어", "speech": "ko-KR", "tts": "ko-KR", "tier": "international", "script": "korean"},
}

# Special code for romanized Hindi in Latin script
HINGLISH = "hinglish"


def name_of(code: str) -> str:
    """Return human-readable English name of language code."""
    if code == HINGLISH:
        return "Hinglish (Hindi in Roman script)"
    return LANGUAGES.get(code, {}).get("name", code)


def native_name_of(code: str) -> str:
    """Return native script name of language code."""
    if code == HINGLISH:
        return "हिंग्लिश / Hinglish"
    return LANGUAGES.get(code, {}).get("native", name_of(code))


def reply_lang(code: str) -> str:
    """Language the assistant should reply in for a detected language."""
    if code == HINGLISH:
        return "hi"
    return code if code in LANGUAGES else "en"
