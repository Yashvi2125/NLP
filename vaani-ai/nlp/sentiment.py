"""Sentiment analysis: VADER for English; translate-then-VADER or a small lexicon for other languages."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .preprocess import tokenize
from .translate import translate

_vader = SentimentIntensityAnalyzer()

# Tiny multilingual lexicon used only when translation is unavailable (offline fallback).
POS = set("""अच्छा अच्छी बढ़िया शानदार खुश प्यार धन्यवाद बहुत_अच्छा मज़ा सुंदर
acha accha badhiya mast khush pyaar shukriya dhanyavad zabardast
bueno buena excelente feliz gracias genial me_encanta amor
bon bien super heureux merci génial excellent
gut toll super glücklich danke fantastisch""".split())
NEG = set("""बुरा बुरी खराब उदास गुस्सा दुखी बेकार नफरत परेशान
bura kharab udaas dukhi gussa bekar pareshan
malo mala terrible triste odio horrible
mauvais mal triste horrible nul
schlecht traurig schrecklich furchtbar""".split())


def _label(c: float) -> str:
    return "positive" if c >= 0.05 else "negative" if c <= -0.05 else "neutral"


def analyze(text: str, lang: str = "en") -> dict:
    """Return {label, compound, scores, method, english_text}."""
    if not text.strip():
        return {"label": "neutral", "compound": 0.0, "scores": {}, "method": "empty", "english_text": ""}

    if lang == "en":
        s = _vader.polarity_scores(text)
        return {"label": _label(s["compound"]), "compound": s["compound"],
                "scores": {k: s[k] for k in ("pos", "neu", "neg")},
                "method": "VADER", "english_text": text}

    tr = translate(text, lang, "en")
    if tr["ok"] and tr["engine"] != "identity" and tr["text"] != text:
        s = _vader.polarity_scores(tr["text"])
        return {"label": _label(s["compound"]), "compound": s["compound"],
                "scores": {k: s[k] for k in ("pos", "neu", "neg")},
                "method": f"translate→VADER ({tr['engine']})", "english_text": tr["text"]}

    toks = tokenize(text)
    pos = sum(t in POS for t in toks)
    neg = sum(t in NEG for t in toks)
    compound = round((pos - neg) / max(1, pos + neg + 1), 3)
    return {"label": _label(compound), "compound": compound,
            "scores": {"pos": pos, "neu": max(0, len(toks) - pos - neg), "neg": neg},
            "method": "multilingual lexicon (offline)", "english_text": tr["text"] if tr["ok"] else ""}
