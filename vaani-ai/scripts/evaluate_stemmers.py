"""Empirical evaluation of Indic stemmers on the held-out test split.

Tests whether:
  1. Pass-through / no stemming on Indic text
  2. Light conservative suffix stemming on Indic text
  3. Aggressive Indic suffix stemming
improves or harms multi-lingual intent classification accuracy and macro F1.
"""

import json
import re
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score
from scipy.sparse import hstack
import joblib

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "processed"
MODEL_PATH = ROOT_DIR / "models" / "intent_model.joblib"

# Hindi suffixes (from Ramanathan & Rao 2003)
HI_SUFFIXES = [
    "ाएं", "ाया", "ेगी", "ेंगे", "ोगी", "ोगे", "ाओ", "िए", "कर", "ने", "नी",
    "या", "ीं", "ाय", "े", "ी", "ा", "ो", "ू", "ें",
]

# Marathi suffixes
MR_SUFFIXES = [
    "यांना", "ातील", "ाच्या", "ावरून", "ांसाठी", "ायचे", "ायला", "ावे",
    "तील", "च्या", "साठी", "वरून", "कडे", "हून", "ला", "ना", "ने", "नी",
    "ात", "चे", "ची", "चा", "वे", "ते", "तात", "ले", "ला", "ली",
]


def stem_indic_conservative(word: str, lang: str) -> str:
    """Light, conservative stemming only removing large inflectional suffixes (> 3 chars)."""
    if len(word) <= 4:
        return word

    suffixes = HI_SUFFIXES if lang in ("hi", "hinglish") else MR_SUFFIXES if lang == "mr" else []
    for suf in suffixes:
        if len(suf) >= 3 and word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[:-len(suf)]
    return word


def stem_indic_aggressive(word: str, lang: str) -> str:
    """Aggressive stemming removing all suffix matches down to 2 chars."""
    if len(word) <= 3:
        return word

    suffixes = HI_SUFFIXES if lang in ("hi", "hinglish") else MR_SUFFIXES if lang == "mr" else []
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= 2:
            return word[:-len(suf)]
    return word


def evaluate():
    print("=" * 60)
    print("Empirical Evaluation of Indic Stemmers on Unseen Test Partition")
    print("=" * 60)

    with open(DATA_DIR / "train.json", "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(DATA_DIR / "test.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)

    # Filter to Indic languages in test data (hi, mr, gu, bn, ta, hinglish)
    indic_langs = {"hi", "mr", "gu", "bn", "ta", "hinglish"}
    test_indic = [item for item in test_data if item["lang"] in indic_langs]
    print(f"Total Indic test samples: {len(test_indic)} / {len(test_data)}")

    # Load baseline model
    model = joblib.load(MODEL_PATH)
    features_step = model.named_steps["features"]
    clf_step = model.named_steps["clf"]

    # 1. Baseline: No Indic Stemming (pure subword char + word n-grams)
    X_raw = [item["text"] for item in test_indic]
    y_true = [item["intent"] for item in test_indic]
    preds_raw = model.predict(X_raw)

    acc_raw = accuracy_score(y_true, preds_raw) * 100
    f1_raw = f1_score(y_true, preds_raw, average="macro", zero_division=0) * 100
    print(f"\n1. Baseline (No Indic Stemming, preserving inflections):")
    print(f"   Accuracy : {acc_raw:.2f}%")
    print(f"   Macro F1 : {f1_raw:.2f}%")

    # 2. Conservative Indic Stemming
    X_cons = []
    for item in test_indic:
        words = item["text"].split()
        stemmed = [stem_indic_conservative(w, item["lang"]) for w in words]
        X_cons.append(" ".join(stemmed))
    preds_cons = model.predict(X_cons)
    acc_cons = accuracy_score(y_true, preds_cons) * 100
    f1_cons = f1_score(y_true, preds_cons, average="macro", zero_division=0) * 100
    print(f"\n2. Conservative Indic Stemming (long suffixes only):")
    print(f"   Accuracy : {acc_cons:.2f}% (delta: {acc_cons - acc_raw:+.2f}%)")
    print(f"   Macro F1 : {f1_cons:.2f}% (delta: {f1_cons - f1_raw:+.2f}%)")

    # 3. Aggressive Indic Stemming
    X_aggr = []
    for item in test_indic:
        words = item["text"].split()
        stemmed = [stem_indic_aggressive(w, item["lang"]) for w in words]
        X_aggr.append(" ".join(stemmed))
    preds_aggr = model.predict(X_aggr)
    acc_aggr = accuracy_score(y_true, preds_aggr) * 100
    f1_aggr = f1_score(y_true, preds_aggr, average="macro", zero_division=0) * 100
    print(f"\n3. Aggressive Indic Stemming (all suffixes):")
    print(f"   Accuracy : {acc_aggr:.2f}% (delta: {acc_aggr - acc_raw:+.2f}%)")
    print(f"   Macro F1 : {f1_aggr:.2f}% (delta: {f1_aggr - f1_raw:+.2f}%)")

    # Specific qualitative examples
    print("\n" + "-" * 60)
    print("Qualitative Inspection of Meaning Alteration:")
    test_words = [
        ("बजाओ (play audio/music)", "hi"),
        ("बजाना (playing)", "hi"),
        ("वाजले (struck/rung - time query)", "mr"),
        ("वाजवा (play - music request)", "mr"),
        ("सांगायचे (wanted to tell)", "mr"),
    ]
    for w, lang in test_words:
        cons = stem_indic_conservative(w.split()[0], lang)
        aggr = stem_indic_aggressive(w.split()[0], lang)
        print(f"  {w:35s} -> Cons: {cons:15s} | Aggr: {aggr:15s}")
    print("=" * 60)


if __name__ == "__main__":
    evaluate()
