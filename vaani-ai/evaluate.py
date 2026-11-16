"""Evaluate the intent classifier (5-fold CV) and language detector. Output is used in the report."""
from collections import Counter
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, f1_score

from nlp.intent import IntentClassifier, load_dataset
from nlp.langid import detect_language

X, y = load_dataset()
print(f"Dataset: {len(X)} utterances, {len(set(y))} intents")
print("Class balance:", dict(Counter(y)))

pred_all, raw_all, true_all = [], [], []
for tr, te in StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X, y):
    clf = IntentClassifier().fit([X[i] for i in tr], [y[i] for i in tr])
    for i in te:
        p = clf.predict(X[i])
        pred_all.append(p["intent"])        # with the 0.30 fallback threshold (as deployed)
        raw_all.append(p["ranked"][0][0])   # raw argmax of the classifier
        true_all.append(y[i])
print(f"\nIntent classification (5-fold CV)")
print(f"  raw classifier : accuracy={accuracy_score(true_all, raw_all):.3f}  macro-F1={f1_score(true_all, raw_all, average='macro'):.3f}")
print(f"  with fallback  : accuracy={accuracy_score(true_all, pred_all):.3f}  macro-F1={f1_score(true_all, pred_all, average='macro'):.3f}")
print(classification_report(true_all, raw_all, zero_division=0))

LANG_TESTS = [("Hello, how are you doing today?", "en"), ("नमस्ते आप कैसे हैं", "hi"),
              ("Hola, ¿cómo estás hoy?", "es"), ("Bonjour, comment allez-vous ?", "fr"),
              ("Guten Morgen, wie geht es dir?", "de"), ("mera naam Yashvi hai aur main theek hoon", "hinglish"),
              ("તમે કેમ છો", "gu"), ("வணக்கம் எப்படி இருக்கிறீர்கள்", "ta"), ("আপনি কেমন আছেন", "bn"),
              ("तुम्ही कसे आहात, मी ठीक आहे", "mr")]
ok = sum(detect_language(t)["code"] == l for t, l in LANG_TESTS)
print(f"Language detection: {ok}/{len(LANG_TESTS)} correct")
for t, l in LANG_TESTS:
    d = detect_language(t)["code"]
    print(f"  {'✓' if d == l else '✗'} expected={l:9s} got={d:9s} {t}")
