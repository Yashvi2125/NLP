"""Compare classifier performance before vs after enhanced preprocessing.

Evaluates on the unseen test split (2,555 samples across 7 languages).
Measures:
  - Overall Accuracy, Macro F1, Weighted F1
  - Per-language Accuracy and Macro F1
  - Per-intent performance
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import joblib
from sklearn.metrics import accuracy_score, f1_score, classification_report

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from nlp.preprocess import normalize, normalize_hinglish_text
DATA_DIR = ROOT_DIR / "data" / "processed"
MODEL_PATH = ROOT_DIR / "models" / "intent_model.joblib"


def load_test():
    with open(DATA_DIR / "test.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def preprocess_text_for_eval(text: str, lang: str) -> str:
    norm = normalize(text)
    if lang in ("hinglish", "custom"):
        norm = normalize_hinglish_text(norm)
    return norm


def main():
    print("=" * 65)
    print("Vaani AI — Classifier Performance: Before vs. After Preprocessing")
    print("=" * 65)

    test_data = load_test()
    model = joblib.load(MODEL_PATH)

    y_true = [item["intent"] for item in test_data]
    langs = [item["lang"] for item in test_data]

    # Mode 1: Before Preprocessing (Raw input passed as-is)
    X_raw = [item["text"] for item in test_data]
    preds_before = model.predict(X_raw)

    acc_before = accuracy_score(y_true, preds_before) * 100
    macro_f1_before = f1_score(y_true, preds_before, average="macro", zero_division=0) * 100
    weighted_f1_before = f1_score(y_true, preds_before, average="weighted", zero_division=0) * 100

    # Mode 2: After Preprocessing (Enhanced Unicode + Hinglish normalization)
    X_clean = [preprocess_text_for_eval(item["text"], item["lang"]) for item in test_data]
    preds_after = model.predict(X_clean)

    acc_after = accuracy_score(y_true, preds_after) * 100
    macro_f1_after = f1_score(y_true, preds_after, average="macro", zero_division=0) * 100
    weighted_f1_after = f1_score(y_true, preds_after, average="weighted", zero_division=0) * 100

    print("\n1. Overall Performance Comparison:")
    print(f"| Metric | Before Preprocessing | After Enhanced Preprocessing | Delta |")
    print(f"| :--- | :---: | :---: | :---: |")
    print(f"| Accuracy | {acc_before:.2f}% | {acc_after:.2f}% | {acc_after - acc_before:+.2f}% |")
    print(f"| Macro F1 | {macro_f1_before:.2f}% | {macro_f1_after:.2f}% | {macro_f1_after - macro_f1_before:+.2f}% |")
    print(f"| Weighted F1 | {weighted_f1_before:.2f}% | {weighted_f1_after:.2f}% | {weighted_f1_after - weighted_f1_before:+.2f}% |")

    # Per-Language Breakdown
    by_lang = defaultdict(lambda: {"true": [], "before": [], "after": []})
    for i, l in enumerate(langs):
        by_lang[l]["true"].append(y_true[i])
        by_lang[l]["before"].append(preds_before[i])
        by_lang[l]["after"].append(preds_after[i])

    print("\n2. Per-Language Accuracy & Macro F1:")
    print(f"| Language | Samples | Accuracy (Before) | Accuracy (After) | Macro F1 (Before) | Macro F1 (After) |")
    print(f"| :--- | :---: | :---: | :---: | :---: | :---: |")
    for l in sorted(by_lang.keys()):
        d = by_lang[l]
        n = len(d["true"])
        a_b = accuracy_score(d["true"], d["before"]) * 100
        a_a = accuracy_score(d["true"], d["after"]) * 100
        f_b = f1_score(d["true"], d["before"], average="macro", zero_division=0) * 100
        f_a = f1_score(d["true"], d["after"], average="macro", zero_division=0) * 100
        print(f"| `{l:8s}` | {n:7d} | {a_b:6.2f}% | {a_a:6.2f}% | {f_b:6.2f}% | {f_a:6.2f}% |")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
