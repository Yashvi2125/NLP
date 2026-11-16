"""Intent classification (TF-IDF + Logistic Regression) and rule-based named-entity recognition."""
import json
import re
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from .preprocess import normalize

DATA = Path(__file__).resolve().parent.parent / "data" / "intents.json"
CONFIDENCE_THRESHOLD = 0.30


EXTRA = [DATA.parent / "intents_mr_gu.json"]  # Marathi + Gujarati utterances


def load_dataset():
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    for f in EXTRA:
        if f.exists():
            for k, v in json.loads(f.read_text(encoding="utf-8")).items():
                raw.setdefault(k, []).extend(v)
    X, y = [], []
    for intent, examples in raw.items():
        for ex in examples:
            X.append(normalize(ex).lower())
            y.append(intent)
    return X, y


class IntentClassifier:
    """Word + character n-gram TF-IDF so it works across scripts and for Hinglish."""

    def __init__(self):
        self.word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), token_pattern=r"[^\s?!.,:@]+")
        self.char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.clf = LogisticRegression(max_iter=2000, C=12, class_weight="balanced")
        self.fitted = False

    def _features(self, texts, fit=False):
        if fit:
            return hstack([self.word_vec.fit_transform(texts), self.char_vec.fit_transform(texts)]).tocsr()
        return hstack([self.word_vec.transform(texts), self.char_vec.transform(texts)]).tocsr()

    def fit(self, X=None, y=None):
        if X is None:
            X, y = load_dataset()
        self.clf.fit(self._features(X, fit=True), y)
        self.fitted = True
        return self

    def predict(self, text: str, top_k: int = 3) -> dict:
        t = normalize(text).lower()
        probs = self.clf.predict_proba(self._features([t]))[0]
        order = np.argsort(probs)[::-1]
        ranked = [[self.clf.classes_[i], round(float(probs[i]), 3)] for i in order[:top_k]]
        intent, conf = ranked[0]
        if conf < CONFIDENCE_THRESHOLD:
            intent = "fallback"
        return {"intent": intent, "confidence": conf, "ranked": ranked}


# ---------------- Named-entity recognition (rule + gazetteer based) ----------------
CITIES = {"mumbai", "delhi", "pune", "bangalore", "bengaluru", "chennai", "kolkata", "hyderabad", "ahmedabad",
          "jaipur", "surat", "nagpur", "london", "paris", "new york", "tokyo", "berlin", "madrid", "dubai"}
LANG_WORDS = {"hindi": "hi", "marathi": "mr", "gujarati": "gu", "bengali": "bn", "tamil": "ta", "spanish": "es",
              "french": "fr", "german": "de", "english": "en", "हिंदी": "hi", "अंग्रेज़ी": "en", "अंग्रेजी": "en"}
_NAME_PATTERNS = [
    r"(?:my name is|i am called|call me|this is|i'm|mera naam(?: hai)?|मेरा नाम(?: है)?|माझे नाव|माझं नाव|મારું નામ|me llamo|je m'appelle|ich heiße)\s+([^\s\d_,.!?;:]+)",
]
_STOP_NAME = {"happy", "sad", "fine", "good", "great", "tired", "hungry", "very", "so", "not", "from", "a", "an"}


def extract_entities(text: str) -> list:
    """Return list of {type, value} for PERSON, LANGUAGE, CITY, EMAIL, PHONE, NUMBER, TIME, DATE."""
    ents = []
    low = text.lower()

    for pat in _NAME_PATTERNS:
        m = re.search(pat, text, flags=re.IGNORECASE | re.UNICODE)
        if m and m.group(1).lower() not in _STOP_NAME:
            ents.append({"type": "PERSON", "value": m.group(1).capitalize()})
            break

    for w, code in LANG_WORDS.items():
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", low):
            ents.append({"type": "LANGUAGE", "value": code})

    for c in CITIES:
        if re.search(rf"\b{re.escape(c)}\b", low):
            ents.append({"type": "CITY", "value": c.title()})

    for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
        ents.append({"type": "EMAIL", "value": m.group()})
    for m in re.finditer(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)", text):
        ents.append({"type": "PHONE", "value": m.group()})
    for m in re.finditer(r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm)\b|\b\d{1,2}:\d{2}\b", low):
        ents.append({"type": "TIME", "value": m.group()})
    for m in re.finditer(r"\b(today|tomorrow|yesterday|aaj|kal|आज|कल)\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", low):
        ents.append({"type": "DATE", "value": m.group()})
    taken = {e["value"] for e in ents if e["type"] in ("PHONE", "TIME", "DATE")}
    for m in re.finditer(r"(?<![\w:/-])\d+(?:\.\d+)?(?![\w:/-])", text):
        if m.group() not in taken and not any(m.group() in t for t in taken):
            ents.append({"type": "NUMBER", "value": m.group()})
    return ents
