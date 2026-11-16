"""Language identification: Unicode-script rules + langdetect + Hinglish heuristic."""
import re
from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from .languages import HINGLISH, LANGUAGES

DetectorFactory.seed = 0  # deterministic results

_SCRIPTS = [  # (regex, language) – these scripts map (almost) uniquely to a language
    (re.compile(r"[઀-૿]"), "gu"),
    (re.compile(r"[஀-௿]"), "ta"),
    (re.compile(r"[ঀ-৿]"), "bn"),
]
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_MR_WORDS = set("आहे आहात आहेस काय मला माझे माझं तुम्ही तुझे तुमचे आणि नाही का होते करू सांगा वाजले कसे".split())
_HI_WORDS = set("है हैं मैं मेरा आप क्या और नहीं को का की के से पर बताओ कैसे हूँ था".split())

# Common romanised-Hindi words used to spot Hinglish (langdetect cannot).
_HINGLISH_WORDS = set("""
hai hain nahi nahin kya kaise kaisa kaun kab kahan kyun kyu mujhe mera meri mere tum tumhara aap aapka
main mai hum acha accha theek thik bahut bohot namaste dhanyavad shukriya batao bolo karo kar raha rahi
abhi aaj kal samay baje naam hoon hu ho se ko ka ki ke mein par aur lekin toh yaar bhai chalo alvida
""".split())


def _hinglish_score(text: str) -> float:
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return 0.0
    return sum(w in _HINGLISH_WORDS for w in words) / len(words)


def detect_language(text: str) -> dict:
    """Return {code, confidence, method, candidates}."""
    text = (text or "").strip()
    if not text:
        return {"code": "en", "confidence": 0.0, "method": "empty", "candidates": []}

    for rx, code in _SCRIPTS:
        if rx.search(text):
            return {"code": code, "confidence": 0.99, "method": "unicode-script", "candidates": [[code, 0.99]]}

    if _DEVANAGARI.search(text):
        try:
            cands = [(c.lang, c.prob) for c in detect_langs(text)]
        except LangDetectException:
            cands = []
        words = re.findall(r"[\u0900-\u097F]+", text)
        mr_hits, hi_hits = sum(w in _MR_WORDS for w in words), sum(w in _HI_WORDS for w in words)
        if mr_hits != hi_hits:  # marker words beat statistical guess on short text
            code = "mr" if mr_hits > hi_hits else "hi"
            return {"code": code, "confidence": 0.9, "method": "script+marker-words",
                    "candidates": [[code, 0.9]]}
        allowed = [(l, p) for l, p in cands if l in ("hi", "mr", "ne")]
        code = allowed[0][0] if allowed else "hi"
        code = "hi" if code == "ne" else code
        conf = allowed[0][1] if allowed else 0.6
        return {"code": code, "confidence": round(conf, 3), "method": "script+langdetect",
                "candidates": [[l, round(p, 3)] for l, p in cands]}

    score = _hinglish_score(text)
    if score >= 0.25:
        return {"code": HINGLISH, "confidence": round(min(0.99, 0.5 + score), 3),
                "method": "hinglish-heuristic", "candidates": [[HINGLISH, round(score, 3)]]}

    try:
        cands = [(c.lang, c.prob) for c in detect_langs(text)]
    except LangDetectException:
        return {"code": "en", "confidence": 0.0, "method": "fallback", "candidates": []}
    top = cands[0]
    code = top[0] if top[0] in LANGUAGES else "en"
    return {"code": code, "confidence": round(top[1], 3), "method": "langdetect",
            "candidates": [[l, round(p, 3)] for l, p in cands]}
