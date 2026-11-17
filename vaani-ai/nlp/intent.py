"""Intent classification (TF-IDF + Logistic Regression) and rule-based named-entity recognition."""
import json
import re
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from .preprocess import normalize

DATA = Path(__file__).resolve().parent.parent / "data" / "intents.json"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "intent_model.joblib"
CONFIDENCE_THRESHOLD = 0.45


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
    """Word + character n-gram TF-IDF so it works across scripts and for Hinglish.
    Loads pre-trained offline model artifact when present to avoid training on startup.
    """

    def __init__(self, model_path: Path = None):
        self.pipeline = None
        self.fitted = False
        self.word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), token_pattern=r"[^\s?!.,:@]+")
        self.char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.clf = LogisticRegression(max_iter=2000, C=12, class_weight="balanced")

        path = model_path or MODEL_PATH
        if path.exists():
            try:
                self.pipeline = joblib.load(path)
                self.clf = self.pipeline.named_steps["clf"]
                # Verify pipeline classes cover all current dataset labels
                raw_data = json.loads(DATA.read_text(encoding="utf-8"))
                if not set(raw_data.keys()).issubset(set(self.clf.classes_)):
                    self.pipeline = None
                    self.fitted = False
                else:
                    self.fitted = True
            except Exception:
                self.pipeline = None
                self.fitted = False

        if not self.fitted:
            self.fit()

    def _features(self, texts, fit=False):
        if fit:
            return hstack([self.word_vec.fit_transform(texts), self.char_vec.fit_transform(texts)]).tocsr()
        return hstack([self.word_vec.transform(texts), self.char_vec.transform(texts)]).tocsr()

    def fit(self, X=None, y=None):
        if X is None:
            X, y = load_dataset()
        self.clf.fit(self._features(X, fit=True), y)
        self.pipeline = None  # in-memory model takes precedence
        self.fitted = True
        return self

    def predict(self, text: str, top_k: int = 3) -> dict:
        t = normalize(text).lower()
        if self.pipeline is not None:
            probs = self.pipeline.predict_proba([t])[0]
            classes = self.pipeline.named_steps["clf"].classes_
        else:
            probs = self.clf.predict_proba(self._features([t]))[0]
            classes = self.clf.classes_

        # Enforce probability normalization: sum(probs) == 1.0
        total_p = float(np.sum(probs))
        if total_p > 0:
            probs = probs / total_p

        order = np.argsort(probs)[::-1]
        ranked = [[str(classes[i]), round(float(probs[i]), 3)] for i in order[:top_k]]
        intent, conf = str(ranked[0][0]), float(ranked[0][1])
        if conf < CONFIDENCE_THRESHOLD:
            intent = "fallback"
            ranked.insert(0, ["fallback", conf])
        # Invariant: predicted intent always equals the highest-ranked alternative
        return {"intent": intent, "confidence": conf, "ranked": ranked}


# ---------------- Named-entity recognition ----------------
# Re-exported from modular nlp.ner for backward compatibility
from .ner import extract_entities, CITIES, LANG_WORDS
