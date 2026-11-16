"""Multi-tier multilingual language identification for Vaani AI.

Supports 18 core and international languages:
- Indic: Hindi (hi), Marathi (mr), Gujarati (gu), Bengali (bn), Tamil (ta), Telugu (te), Urdu (ur), Hinglish (hinglish).
- European: English (en), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), Dutch (nl), Russian (ru).
- Asian & Middle Eastern: Arabic (ar), Japanese (ja), Chinese Simplified (zh), Korean (ko).

Architecture:
  Tier 0: Empty and whitespace guard
  Tier 1: High-precision Unicode script detection (Gujarati, Tamil, Telugu, Bengali, Korean, Japanese, Chinese, Arabic, Cyrillic)
  Tier 2: Devanagari lexical & grammatical disambiguation (Hindi vs. Marathi)
  Tier 3: Latin script disambiguation:
          - Romanized Hindi (Hinglish) heuristic & code-mixing scorer
          - Curated short-phrase lexicon for greetings and common queries across European languages
          - Calibrated statistical n-gram model (langdetect) with fallback handling
  Tier 4: Mixed-language / code-switching detection & candidate ranking
"""

import re
from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from .languages import HINGLISH, LANGUAGES

DetectorFactory.seed = 0  # deterministic output

# ---------------- Tier 1: Distinctive Unicode Script Regexes ----------------
_RX_GUJARATI = re.compile(r"[\u0A80-\u0AFF]")
_RX_TAMIL = re.compile(r"[\u0B80-\u0BFF]")
_RX_TELUGU = re.compile(r"[\u0C00-\u0C7F]")
_RX_BENGALI = re.compile(r"[\u0980-\u09FF]")
_RX_KOREAN = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]")
_RX_JAPANESE_KANA = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")
_RX_HANZI = re.compile(r"[\u4E00-\u9FFF]")
_RX_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_RX_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")
_RX_URDU_MARKERS = re.compile(r"[ٹڈڑںےہ]")

# Devanagari range
_RX_DEVANAGARI = re.compile(r"[\u0900-\u097F]")

# ---------------- Tier 2: Devanagari Marker Words ----------------
_MR_WORDS = {
    "आहे", "आहेत", "आहात", "आहेस", "काय", "मला", "माझे", "माझं", "तुम्ही", "तुझे",
    "तुमचे", "आणि", "नाही", "का", "होते", "होती", "होता", "करू", "सांगा", "वाजले",
    "वाजवा", "कसे", "कसा", "कशी", "नवीन", "मंडळी", "काळजी", "घ्या", "भेटू", "लवकर",
    "करायचे", "बोला", "दिवस", "वार", "तिथी", "हवामान", "पाऊस", "सांग",
}
_HI_WORDS = {
    "है", "हैं", "हूँ", "था", "थे", "थी", "मैं", "मेरा", "मेरी", "मेरे", "आप",
    "क्या", "और", "नहीं", "को", "का", "की", "के", "से", "पर", "बताओ", "कैसे",
    "कहाँ", "कहा", "क्यो", "क्यों", "चाहिए", "रहा", "रहे", "रही", "गाना", "बजाओ",
    "सुनाओ", "तारीख", "समय", "मौसम", "हाल", "दिन", "नाम", "दोस्त", "नमस्ते",
}

# ---------------- Tier 3: Hinglish Lexicon ----------------
_HINGLISH_WORDS = {
    "hai", "hain", "nahi", "nahin", "kya", "kaise", "kaisa", "kaisi", "kaun",
    "kab", "kahan", "kyun", "kyu", "mujhe", "mera", "meri", "mere", "tum",
    "tumhara", "aap", "aapka", "main", "mai", "hum", "acha", "accha", "theek",
    "thik", "bahut", "bohot", "namaste", "dhanyavad", "shukriya", "batao",
    "bolo", "karo", "kar", "raha", "rahe", "rahi", "abhi", "aaj", "kal", "samay",
    "baje", "naam", "hoon", "hu", "ho", "se", "ko", "ka", "ki", "ke", "mein",
    "par", "aur", "lekin", "toh", "yaar", "bhai", "chalo", "alvida", "sunao",
    "bajao", "gaana", "gana", "chutkula", "mausam", "kuch", "sab", "apna", "apne",
    "dost", "kripya", "theek", "shandar", "zaroor", "bolo", "bata",
}

# ---------------- Tier 3: Short-Phrase European Lexicons ----------------
# High-precision unambiguous salutations, affirmative words, and common phrases
_SHORT_PHRASE_LEXICON = {
    "pt": {
        "olá", "ola", "olá amigo", "ola amigo", "bom dia", "boa tarde", "boa noite",
        "obrigado", "obrigada", "muito obrigado", "por favor", "como vai",
        "como você está", "adeus", "até logo", "tudo bem", "sim", "que horas são",
    },
    "es": {
        "hola", "hola amigo", "hola amiga", "buenos días", "buenas tardes",
        "buenas noches", "gracias", "muchas gracias", "por favor", "cómo estás",
        "como estas", "adiós", "adios", "hasta luego", "hasta pronto", "sí",
        "amigo", "amiga", "qué hora es",
    },
    "nl": {
        "hallo dag", "dag", "goedemorgen", "goedemiddag", "goedenavond", "goedenacht",
        "dank je", "dank u", "dankjewel", "alsjeblieft", "alstublieft",
        "hoe gaat het", "tot ziens", "ja", "nee", "hoe laat is het", "lekker",
    },
    "de": {
        "hallo", "guten morgen", "guten tag", "guten abend", "gute nacht",
        "danke", "danke schön", "vielen dank", "bitte", "tschüss", "auf wiedersehen",
        "wie geht es dir", "wie gehts", "wie spät ist es", "ja", "nein", "wunderbar",
    },
    "fr": {
        "bonjour", "salut", "bonsoir", "bonne nuit", "merci", "merci beaucoup",
        "au revoir", "s'il vous plaît", "comment allez-vous", "comment vas-tu",
        "oui", "non", "très bien", "s'il vous plait", "enchanté", "bienvenue",
    },
    "it": {
        "ciao", "ciao amico", "buongiorno", "buonasera", "buonanotte", "grazie",
        "grazie mille", "prego", "per favore", "come stai", "come va", "arrivederci",
        "a presto", "sì", "che ore sono", "molto bene",
    },
    "ru": {
        "привет", "здравствуйте", "доброе утро", "добрый день", "добрый вечер",
        "спокойной ночи", "спасибо", "большое спасибо", "пожалуйста", "до свидания",
        "пока", "как дела", "да", "нет", "который час",
    },
    "en": {
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "good night", "goodbye", "bye", "thanks", "thank you", "thank you so much",
        "please", "how are you", "what time is it", "what is today's date",
        "tell me a joke", "yes", "no", "great", "wonderful", "cool",
    },
}


def _clean_for_lookup(text: str) -> str:
    """Normalize text into lowercase alphanumeric space-collapsed tokens for lookup."""
    low = text.lower().strip()
    return re.sub(r"[^\w\s]", "", low)


def _check_short_phrase_lexicon(text: str) -> tuple[str | None, float]:
    """Check if input directly matches a known distinctive short phrase or greeting."""
    cleaned = _clean_for_lookup(text)
    if not cleaned:
        return None, 0.0

    padded = f" {cleaned} "
    # 1. Exact match or phrase match
    for lang, phrases in _SHORT_PHRASE_LEXICON.items():
        for p in phrases:
            if p == cleaned or f" {p} " in padded:
                return lang, 0.98

    # 2. Distinctive single-word salutations (for short inputs <= 4 words)
    words = cleaned.split()
    if len(words) <= 4:
        distinctive_salutations = {
            "bonjour": "fr", "salut": "fr", "merci": "fr",
            "hola": "es", "adiós": "es", "adios": "es", "gracias": "es",
            "ciao": "it", "grazie": "it",
            "olá": "pt", "ola": "pt", "obrigado": "pt", "obrigada": "pt",
            "danke": "de", "tschüss": "de", "bitte": "de",
            "dag": "nl", "dankjewel": "nl",
            "привет": "ru", "спасибо": "ru",
        }
        for w in words:
            if w in distinctive_salutations:
                return distinctive_salutations[w], 0.96

    return None, 0.0


def _hinglish_score(text: str) -> float:
    """Compute lexical density of romanized Hindi tokens."""
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return 0.0
    matches = sum(w in _HINGLISH_WORDS for w in words)
    return matches / len(words)


def detect_language(text: str) -> dict:
    """Robust multi-tier language detection returning {code, name, confidence, method, is_mixed, candidates}."""
    text = (text or "").strip()
    if not text:
        return {
            "code": "en",
            "name": LANGUAGES["en"]["name"],
            "confidence": 0.0,
            "method": "empty-fallback",
            "is_mixed": False,
            "candidates": [["en", 0.0]],
        }

    # ---------------- Tier 1: Distinctive Unicode Scripts ----------------
    if _RX_JAPANESE_KANA.search(text):
        return {
            "code": "ja",
            "name": LANGUAGES["ja"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:japanese",
            "is_mixed": False,
            "candidates": [["ja", 0.99]],
        }

    if _RX_KOREAN.search(text):
        return {
            "code": "ko",
            "name": LANGUAGES["ko"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:korean",
            "is_mixed": False,
            "candidates": [["ko", 0.99]],
        }

    if _RX_GUJARATI.search(text):
        return {
            "code": "gu",
            "name": LANGUAGES["gu"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:gujarati",
            "is_mixed": False,
            "candidates": [["gu", 0.99]],
        }

    if _RX_TAMIL.search(text):
        return {
            "code": "ta",
            "name": LANGUAGES["ta"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:tamil",
            "is_mixed": False,
            "candidates": [["ta", 0.99]],
        }

    if _RX_TELUGU.search(text):
        return {
            "code": "te",
            "name": LANGUAGES["te"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:telugu",
            "is_mixed": False,
            "candidates": [["te", 0.99]],
        }

    if _RX_BENGALI.search(text):
        return {
            "code": "bn",
            "name": LANGUAGES["bn"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:bengali",
            "is_mixed": False,
            "candidates": [["bn", 0.99]],
        }

    if _RX_HANZI.search(text):
        # Chinese characters without Japanese Kana
        return {
            "code": "zh",
            "name": LANGUAGES["zh"]["name"],
            "confidence": 0.98,
            "method": "unicode-script:chinese",
            "is_mixed": False,
            "candidates": [["zh", 0.98]],
        }

    if _RX_ARABIC.search(text):
        # Disambiguate Urdu vs Arabic
        if _RX_URDU_MARKERS.search(text):
            return {
                "code": "ur",
                "name": LANGUAGES["ur"]["name"],
                "confidence": 0.96,
                "method": "script+urdu-markers",
                "is_mixed": False,
                "candidates": [["ur", 0.96], ["ar", 0.04]],
            }
        return {
            "code": "ar",
            "name": LANGUAGES["ar"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:arabic",
            "is_mixed": False,
            "candidates": [["ar", 0.99]],
        }

    if _RX_CYRILLIC.search(text):
        return {
            "code": "ru",
            "name": LANGUAGES["ru"]["name"],
            "confidence": 0.99,
            "method": "unicode-script:cyrillic",
            "is_mixed": False,
            "candidates": [["ru", 0.99]],
        }

    # ---------------- Tier 2: Devanagari (Hindi vs. Marathi) ----------------
    if _RX_DEVANAGARI.search(text):
        dev_words = re.findall(r"[\u0900-\u097F]+", text)
        mr_hits = sum(w in _MR_WORDS for w in dev_words)
        hi_hits = sum(w in _HI_WORDS for w in dev_words)

        if mr_hits > hi_hits:
            return {
                "code": "mr",
                "name": LANGUAGES["mr"]["name"],
                "confidence": 0.95,
                "method": "script+marathi-markers",
                "is_mixed": False,
                "candidates": [["mr", 0.95], ["hi", 0.05]],
            }
        elif hi_hits > mr_hits:
            return {
                "code": "hi",
                "name": LANGUAGES["hi"]["name"],
                "confidence": 0.95,
                "method": "script+hindi-markers",
                "is_mixed": False,
                "candidates": [["hi", 0.95], ["mr", 0.05]],
            }

        # Statistical fallback for Devanagari using langdetect
        try:
            cands = [(c.lang, c.prob) for c in detect_langs(text)]
        except LangDetectException:
            cands = []
        filtered = [(l, p) for l, p in cands if l in ("hi", "mr", "ne")]
        top_code = filtered[0][0] if filtered else "hi"
        top_code = "hi" if top_code == "ne" else top_code
        top_conf = round(filtered[0][1], 3) if filtered else 0.75

        return {
            "code": top_code,
            "name": LANGUAGES[top_code]["name"],
            "confidence": top_conf,
            "method": "script+statistical-devanagari",
            "is_mixed": False,
            "candidates": [[l, round(p, 3)] for l, p in cands],
        }

    # ---------------- Tier 3: Latin Script (Hinglish vs. European vs. English) ----------------
    # 1. Hinglish check
    h_score = _hinglish_score(text)
    latin_words = re.findall(r"[a-z']+", text.lower())

    # If sentence is short (<= 3 words) or contains explicit code-switching Hindi markers
    # e.g., 'mera naam', 'kaise ho', 'dhanyavad', 'dost', 'bhai'
    has_strong_hinglish = any(w in _HINGLISH_WORDS for w in latin_words)
    hinglish_markers = {"dost", "bhai", "yaar", "naam", "kaise", "kaisa", "kya", "batao", "dhanyavad", "shukriya", "namaste"}
    has_explicit_code_switch = any(w in hinglish_markers for w in latin_words)

    if (h_score >= 0.20) or has_explicit_code_switch or (len(latin_words) <= 3 and has_strong_hinglish and not any(w in _SHORT_PHRASE_LEXICON.get("en", set()) for w in latin_words)):
        conf = round(min(0.99, max(0.88, 0.6 + h_score)), 3)
        return {
            "code": HINGLISH,
            "name": "Hinglish (Hindi in Roman script)",
            "confidence": conf,
            "method": "hinglish-heuristic",
            "is_mixed": any(ch for ch in text if _is_indic_char_or_accent(ch)) or (len(latin_words) > 1 and h_score < 0.8),
            "candidates": [[HINGLISH, conf], ["en", round(1.0 - conf, 3)]],
        }

    # 2. Short-phrase distinctive lookup for European greetings/queries
    short_lang, short_conf = _check_short_phrase_lexicon(text)
    if short_lang:
        return {
            "code": short_lang,
            "name": LANGUAGES[short_lang]["name"],
            "confidence": short_conf,
            "method": "short-phrase-lexicon",
            "is_mixed": False,
            "candidates": [[short_lang, short_conf]],
        }

    # 3. Statistical character n-gram model (langdetect)
    try:
        cands = [(c.lang, c.prob) for c in detect_langs(text)]
    except LangDetectException:
        return {
            "code": "en",
            "name": LANGUAGES["en"]["name"],
            "confidence": 0.30,
            "method": "fallback:english",
            "is_mixed": False,
            "candidates": [["en", 0.30]],
        }

    # Check for code-switching / mixed language in candidates
    is_mixed = len(cands) > 1 and cands[1][1] >= 0.25
    top_cand = cands[0]
    top_lang = top_cand[0]

    # Map aliases / compatible codes
    if top_lang == "zh-cn":
        top_lang = "zh"

    # Verify language is in supported registry
    final_lang = top_lang if top_lang in LANGUAGES else "en"
    final_conf = round(top_cand[1], 3)

    return {
        "code": final_lang,
        "name": LANGUAGES[final_lang]["name"],
        "confidence": final_conf,
        "method": "statistical:langdetect",
        "is_mixed": is_mixed,
        "candidates": [[l, round(p, 3)] for l, p in cands],
    }


def _is_indic_char_or_accent(ch: str) -> bool:
    cp = ord(ch)
    return (0x0900 <= cp <= 0x0D7F) or (cp in (0x00E0, 0x00E8, 0x00E9, 0x00F1, 0x00FC, 0x00E4, 0x00F6))
