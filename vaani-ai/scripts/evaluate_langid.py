"""Comprehensive Evaluation of Multi-Tier Language Identification.

Tests all 18 languages:
  Core Indian: en, hi, mr, gu, bn, ta, te, ur, hinglish
  European: es, fr, de, it, pt, nl, ru
  Asian & Middle Eastern: ar, ja, zh, ko

Evaluates across:
  1. Standard/Normal full sentences
  2. Short utterances (1-3 words)
  3. Ambiguous & edge case inputs
  4. Mixed-language & code-switched inputs
"""

import sys
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from nlp.langid import detect_language
from nlp.languages import LANGUAGES, HINGLISH

# Benchmark Test Suite across all 18 languages
LANG_BENCHMARK = [
    # --- Standard / Full Sentences ---
    ("Hello, how are you doing today?", "en", "standard"),
    ("I would like to set an alarm for tomorrow morning.", "en", "standard"),
    ("नमस्ते, आप आज कैसे हैं?", "hi", "standard"),
    ("मुझे नई दिल्ली का मौसम बताओ।", "hi", "standard"),
    ("तुम्ही कसे आहात, मला आजची तारीख सांगा.", "mr", "standard"),
    ("पुण्यात आज पाऊस पडेल का ते सांगा.", "mr", "standard"),
    ("નમસ્તે, તમે કેમ છો? મને આજનો સમય કહો.", "gu", "standard"),
    ("અમદાવાદમાં હવામાન કેવું રહેશે આજે?", "gu", "standard"),
    ("আপনি কেমন আছেন? আমাকে আজকের সময় বলুন।", "bn", "standard"),
    ("আজকের আবহাওয়া কেমন থাকবে?", "bn", "standard"),
    ("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "ta", "standard"),
    ("இன்றைய வானிலை எப்படி இருக்கிறது?", "ta", "standard"),
    ("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te", "standard"),
    ("నాకు ప్రస్తుత సమయం చెప్పండి.", "te", "standard"),
    ("آپ کیسے ہیں؟ مجھے آج کا وقت بتائیں۔", "ur", "standard"),
    ("کیا کل بارش ہوگی؟", "ur", "standard"),
    ("Hola, ¿cómo estás hoy? Quiero saber la hora.", "es", "standard"),
    ("¿Qué tiempo hace en Madrid hoy?", "es", "standard"),
    ("Bonjour, comment allez-vous aujourd'hui ?", "fr", "standard"),
    ("Pouvez-vous me dire l'heure qu'il est ?", "fr", "standard"),
    ("Guten Morgen, wie geht es dir heute?", "de", "standard"),
    ("Kannst du mir bitte einen Witz erzählen?", "de", "standard"),
    ("Ciao, come stai oggi? Che ore sono a Roma?", "it", "standard"),
    ("Vorrei sapere che tempo fa a Milano oggi.", "it", "standard"),
    ("Olá, como você está? Gostaria de saber as horas.", "pt", "standard"),
    ("Qual é a previsão do tempo para o Rio de Janeiro?", "pt", "standard"),
    ("Hallo, hoe gaat het met je vandaag?", "nl", "standard"),
    ("Kun je me vertellen hoe laat het is?", "nl", "standard"),
    ("Привет, как твои дела сегодня?", "ru", "standard"),
    ("Какая погода сегодня в Москве?", "ru", "standard"),
    ("مرحبا، كيف حالك اليوم؟ ما هو الوقت الآن؟", "ar", "standard"),
    ("ما هي حالة الطقس اليوم في القاهرة؟", "ar", "standard"),
    ("こんにちは、今日はお元気ですか？今何時ですか？", "ja", "standard"),
    ("今日の東京の天気を教えてください。", "ja", "standard"),
    ("你好，今天天气怎么样？现在几点了？", "zh", "standard"),
    ("请给我讲一个好笑的笑话。", "zh", "standard"),
    ("안녕하세요, 오늘 어떻게 지내세요?", "ko", "standard"),
    ("오늘 서울 날씨는 어떤가요?", "ko", "standard"),
    ("mera naam Rahul hai aur main theek hoon", "hinglish", "standard"),
    ("aaj ka mausam kaisa hai bhai batao na", "hinglish", "standard"),

    # --- Short Utterances (1-3 words) ---
    ("Good morning", "en", "short"),
    ("Thank you", "en", "short"),
    ("नमस्ते दोस्त", "hi", "short"),
    ("समय बताओ", "hi", "short"),
    ("किती वाजले", "mr", "short"),
    ("नवीन काय", "mr", "short"),
    ("કેમ છો", "gu", "short"),
    ("આભાર", "gu", "short"),
    ("ধন্যবাদ", "bn", "short"),
    ("কেমন আছেন", "bn", "short"),
    ("வணக்கம்", "ta", "short"),
    ("நன்றி", "ta", "short"),
    ("నమస్కారం", "te", "short"),
    ("ధన్యవాదాలు", "te", "short"),
    ("شکریہ", "ur", "short"),
    ("بہت خوب", "ur", "short"),
    ("Hola amigo", "es", "short"),
    ("Muchas gracias", "es", "short"),
    ("Bonjour", "fr", "short"),
    ("Merci beaucoup", "fr", "short"),
    ("Guten Tag", "de", "short"),
    ("Danke schön", "de", "short"),
    ("Ciao amico", "it", "short"),
    ("Grazie mille", "it", "short"),
    ("Olá amigo", "pt", "short"),
    ("Muito obrigado", "pt", "short"),
    ("Hallo dag", "nl", "short"),
    ("Dank je", "nl", "short"),
    ("Привет", "ru", "short"),
    ("Большое спасибо", "ru", "short"),
    ("مرحبا", "ar", "short"),
    ("شكرا جزيلا", "ar", "short"),
    ("こんにちは", "ja", "short"),
    ("ありがとう", "ja", "short"),
    ("你好", "zh", "short"),
    ("谢谢", "zh", "short"),
    ("안녕하세요", "ko", "short"),
    ("감사합니다", "ko", "short"),
    ("namaste bhai", "hinglish", "short"),
    ("bahut shukriya", "hinglish", "short"),
    ("kaise ho", "hinglish", "short"),

    # --- Code-Switching & Mixed Inputs ---
    ("Please mujhe time batao", "hinglish", "mixed"),
    ("Today ka weather kaisa hai?", "hinglish", "mixed"),
    ("Thank you so much dost", "hinglish", "mixed"),
    ("Hello दोस्त कैसे हो", "hi", "mixed"),
]


def evaluate_langid():
    print("=" * 70)
    print("Vaani AI — Comprehensive Multilingual Language Identification Evaluation")
    print("=" * 70)

    total = len(LANG_BENCHMARK)
    y_true = []
    y_pred = []
    confs = []
    by_category = defaultdict(lambda: {"correct": 0, "total": 0})
    by_lang = defaultdict(lambda: {"correct": 0, "total": 0})
    failures = []

    for text, expected, cat in LANG_BENCHMARK:
        res = detect_language(text)
        pred = res["code"]
        conf = res["confidence"]

        y_true.append(expected)
        y_pred.append(pred)
        confs.append(conf)

        is_ok = (pred == expected)
        by_category[cat]["total"] += 1
        by_lang[expected]["total"] += 1
        if is_ok:
            by_category[cat]["correct"] += 1
            by_lang[expected]["correct"] += 1
        else:
            failures.append({
                "text": text,
                "expected": expected,
                "predicted": pred,
                "confidence": conf,
                "method": res["method"],
                "category": cat,
            })

    overall_acc = accuracy_score(y_true, y_pred) * 100
    macro_p = precision_score(y_true, y_pred, average="macro", zero_division=0) * 100
    macro_r = recall_score(y_true, y_pred, average="macro", zero_division=0) * 100
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) * 100
    avg_conf = sum(confs) / len(confs) * 100

    print("\n1. Overall Evaluation Metrics:")
    print(f"| Metric | Score |")
    print(f"| :--- | :---: |")
    print(f"| Total Benchmark Utterances | {total} |")
    print(f"| Correctly Identified | {sum(1 for t, p in zip(y_true, y_pred) if t == p)} / {total} |")
    print(f"| **Overall Accuracy** | **{overall_acc:.2f}%** |")
    print(f"| **Macro Precision** | **{macro_p:.2f}%** |")
    print(f"| **Macro Recall** | **{macro_r:.2f}%** |")
    print(f"| **Macro F1 Score** | **{macro_f1:.2f}%** |")
    print(f"| **Mean Prediction Confidence** | **{avg_conf:.1f}%** |")

    print("\n2. Performance by Input Category:")
    print(f"| Category | Total Samples | Correct | Accuracy |")
    print(f"| :--- | :---: | :---: | :---: |")
    for cat, d in sorted(by_category.items()):
        acc = (d["correct"] / d["total"]) * 100
        print(f"| `{cat:12s}` | {d['total']:13d} | {d['correct']:7d} | {acc:7.2f}% |")

    print("\n3. Per-Language Accuracy Breakdown:")
    print(f"| Language Code | Language Name | Samples | Correct | Accuracy | Support Tier |")
    print(f"| :--- | :--- | :---: | :---: | :---: | :--- |")
    for l in sorted(by_lang.keys()):
        d = by_lang[l]
        acc = (d["correct"] / d["total"]) * 100
        tier = LANGUAGES.get(l, {}).get("tier", "core")
        name = "Hinglish (Roman Hindi)" if l == HINGLISH else LANGUAGES.get(l, {}).get("name", l)
        print(f"| `{l:9s}` | {name:24s} | {d['total']:7d} | {d['correct']:7d} | {acc:7.2f}% | {tier.capitalize()} |")

    if failures:
        print("\n4. Failure Cases Analysis:")
        for f in failures:
            print(f"  [FAIL] Expected: {f['expected']:8s} | Got: {f['predicted']:8s} (conf: {f['confidence']:.2f}, method: {f['method']}) | '{f['text']}'")
    else:
        print("\n4. Failure Cases: ZERO failures across all benchmark categories!")

    print("=" * 70)


if __name__ == "__main__":
    evaluate_langid()
