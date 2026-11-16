"""Multilingual Sentiment Analysis Evaluation Suite for Vaani AI.

Evaluates sentiment analysis across all 20 languages:
- English, Hindi, Marathi, Gujarati, Hinglish, Bengali, Tamil, Telugu, Urdu
- Spanish, French, German, Italian, Portuguese, Dutch, Russian, Arabic, Japanese, Chinese, Korean

Tests:
  - Positive utterances
  - Negative utterances
  - Neutral / factual queries
  - Negation reversal (e.g. 'अच्छा नहीं है' -> negative)
  - Intensifiers (e.g. 'बहुत अच्छा' -> boosted compound)
  - Emojis (e.g. '❤️', '😭', '👍', '😡')
"""

import sys
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from nlp.sentiment import analyze
from nlp.languages import LANGUAGES, HINGLISH

# Benchmark dataset for multilingual sentiment
SENTIMENT_BENCHMARK = [
    # English
    ("I love this assistant, it is wonderful!", "en", "positive"),
    ("This is a terrible and awful mistake.", "en", "negative"),
    ("The train leaves at 5:30 pm today.", "en", "neutral"),
    ("This is not good at all.", "en", "negative"),  # negation
    ("I am so happy today! 😊❤️", "en", "positive"),  # emoji

    # Hindi
    ("यह बहुत अच्छा और सुंदर है।", "hi", "positive"),
    ("मुझे बहुत बुरा और दुखद लगा।", "hi", "negative"),
    ("आज शुक्रवार है और समय तीन बजे हैं।", "hi", "neutral"),
    ("यह काम बिल्कुल अच्छा नहीं है।", "hi", "negative"),  # negation
    ("आज बहुत उदास हूँ 😭", "hi", "negative"),  # emoji

    # Marathi
    ("हा प्रकल्प अतिशय छान आणि सुंदर आहे.", "mr", "positive"),
    ("मला फार वाईट आणि दुःख झाले.", "mr", "negative"),
    ("उद्या सकाळी सात वाजता गजर लावा.", "mr", "neutral"),
    ("हे मला मुळीच आवडले नाही.", "mr", "negative"),  # negation

    # Gujarati
    ("આ ખૂબ સરસ અને સુંદર છે.", "gu", "positive"),
    ("મને બહુ ખરાબ અને દુઃખ લાગ્યું.", "gu", "negative"),
    ("આજની તારીખ શું છે તે જણાવો.", "gu", "neutral"),
    ("આ સારું નથી.", "gu", "negative"),  # negation

    # Hinglish
    ("aaj main bohot khush aur excited hoon!", "hinglish", "positive"),
    ("yeh bohot bekar aur ghatiya tha yaar", "hinglish", "negative"),
    ("kya time ho raha hai abhi batao", "hinglish", "neutral"),
    ("yeh bilkul acha nahi hai", "hinglish", "negative"),  # negation

    # Bengali
    ("এটি খুব ভালো এবং সুন্দর হয়েছে।", "bn", "positive"),
    ("আমার খুব খারাপ লাগছে এবং কষ্ট হচ্ছে।", "bn", "negative"),
    ("কলকাতার আবহাওয়া কেমন আছে?", "bn", "neutral"),

    # Tamil
    ("இது மிகவும் நல்ல மற்றும் அழகான ஒன்று.", "ta", "positive"),
    ("எனக்கு மிகவும் மோசமான மற்றும் கவலையான நாள்.", "ta", "negative"),
    ("இன்றைய தேதி என்ன?", "ta", "neutral"),

    # Telugu
    ("ఇది చాలా మంచి మరియు అద్భుతంగా ఉంది.", "te", "positive"),
    ("నాకు చాలా బాధ మరియు అసంతృప్తిగా ఉంది.", "te", "negative"),
    ("సమయం ఎంత అయింది?", "te", "neutral"),

    # Urdu
    ("یہ بہت اچھا اور خوبصورت ہے۔", "ur", "positive"),
    ("مجھے بہت برا اور دکھ محسوس ہو رہا ہے۔", "ur", "negative"),
    ("آج کی تاریخ کیا ہے؟", "ur", "neutral"),

    # Spanish
    ("¡Me encanta este lugar, es maravilloso y genial!", "es", "positive"),
    ("Es una experiencia terrible, la peor y muy mala.", "es", "negative"),
    ("El tren llega a las diez de la mañana.", "es", "neutral"),
    ("Esto no es bueno.", "es", "negative"),  # negation

    # French
    ("C'est vraiment magnifique, j'adore et c'est génial !", "fr", "positive"),
    ("C'est une situation horrible, affreuse et très mauvaise.", "fr", "negative"),
    ("La réunion commence à quatorze heures.", "fr", "neutral"),
    ("Ce n'est pas bon du tout.", "fr", "negative"),  # negation

    # German
    ("Das ist wirklich wunderbar, fantastisch und super!", "de", "positive"),
    ("Das ist furchtbar, schrecklich und sehr schlecht.", "de", "negative"),
    ("Der Bus fährt um acht Uhr morgens ab.", "de", "neutral"),
    ("Das ist nicht gut.", "de", "negative"),  # negation

    # Italian
    ("Questo posto è bellissimo, meraviglioso e ottimo!", "it", "positive"),
    ("È un'esperienza orribile, terribile e cattiva.", "it", "negative"),
    ("Che ore sono a Milano adesso?", "it", "neutral"),

    # Portuguese
    ("Isso é maravilhoso, muito bom e excelente!", "pt", "positive"),
    ("Foi uma experiência horrível, péssima e muito ruim.", "pt", "negative"),
    ("O voo sai às nove horas da manhã.", "pt", "neutral"),

    # Dutch
    ("Dit is echt geweldig, mooi en uitstekend!", "nl", "positive"),
    ("Het is verschrikkelijk, heel slecht en naar.", "nl", "negative"),
    ("Hoe laat vertrekt de trein vandaag?", "nl", "neutral"),

    # Russian
    ("Это действительно прекрасно, отлично и замечательно!", "ru", "positive"),
    ("Это ужасно, отвратительно и очень плохо.", "ru", "negative"),
    ("Сколько сейчас времени в Москве?", "ru", "neutral"),

    # Arabic
    ("هذا رائع جدا وجميل وممتاز!", "ar", "positive"),
    ("هذا سيء للغاية وفظيع وقبيح.", "ar", "negative"),
    ("كم الساعة الآن في القاهرة؟", "ar", "neutral"),

    # Japanese
    ("これは本当に素晴らしい、最高で嬉しいです！", "ja", "positive"),
    ("これは最悪で、酷くて悲しいです。", "ja", "negative"),
    ("今の東京の時間を教えてください。", "ja", "neutral"),

    # Chinese
    ("这太棒了，非常优秀，我很开心！", "zh", "positive"),
    ("这太糟糕了，非常差，很难过。", "zh", "negative"),
    ("今天北京的天气怎么样？", "zh", "neutral"),

    # Korean
    ("이것은 정말 훌륭하고 최고로 행복합니다!", "ko", "positive"),
    ("이것은 최악이고 끔찍하며 슬픕니다.", "ko", "negative"),
    ("오늘 서울의 날씨는 어떤가요?", "ko", "neutral"),
]


def evaluate():
    print("=" * 70)
    print("Vaani AI — Multilingual Sentiment Analysis Evaluation Suite")
    print("=" * 70)

    y_true = []
    y_pred = []
    by_lang = defaultdict(lambda: {"correct": 0, "total": 0})
    failures = []

    for text, lang, expected in SENTIMENT_BENCHMARK:
        res = analyze(text, lang)
        pred = res["label"]

        y_true.append(expected)
        y_pred.append(pred)

        by_lang[lang]["total"] += 1
        if pred == expected:
            by_lang[lang]["correct"] += 1
        else:
            failures.append({
                "text": text,
                "lang": lang,
                "expected": expected,
                "predicted": pred,
                "compound": res["compound"],
                "method": res["method"],
            })

    acc = accuracy_score(y_true, y_pred) * 100
    macro_p = precision_score(y_true, y_pred, average="macro", zero_division=0) * 100
    macro_r = recall_score(y_true, y_pred, average="macro", zero_division=0) * 100
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) * 100

    print(f"\n1. Overall Sentiment Evaluation Metrics (Across 20 Languages):")
    print(f"| Metric | Score |")
    print(f"| :--- | :---: |")
    print(f"| Total Benchmark Utterances | {len(SENTIMENT_BENCHMARK)} |")
    print(f"| Correctly Classified | {sum(1 for t, p in zip(y_true, y_pred) if t == p)} / {len(SENTIMENT_BENCHMARK)} |")
    print(f"| **Overall Accuracy** | **{acc:.2f}%** |")
    print(f"| **Macro Precision** | **{macro_p:.2f}%** |")
    print(f"| **Macro Recall** | **{macro_r:.2f}%** |")
    print(f"| **Macro F1 Score** | **{macro_f1:.2f}%** |")

    print(f"\n2. Per-Language Sentiment Accuracy Breakdown:")
    print(f"| Language Code | Language Name | Samples | Correct | Accuracy | Support Tier |")
    print(f"| :--- | :--- | :---: | :---: | :---: | :--- |")
    for l in sorted(by_lang.keys()):
        d = by_lang[l]
        l_acc = (d["correct"] / d["total"]) * 100
        tier = LANGUAGES.get(l, {}).get("tier", "core")
        name = "Hinglish" if l == HINGLISH else LANGUAGES.get(l, {}).get("name", l)
        print(f"| `{l:9s}` | {name:20s} | {d['total']:7d} | {d['correct']:7d} | {l_acc:7.2f}% | {tier.capitalize()} |")

    if failures:
        print("\n3. Failure Analysis:")
        for f in failures:
            print(f"  [FAIL] {f['lang']:8s} | Expected: {f['expected']:8s} | Got: {f['predicted']:8s} (score: {f['compound']:+.2f}, {f['method']}) | '{f['text']}'")
    else:
        print("\n3. Failure Analysis: ZERO failures across all tested languages!")

    print("=" * 70)


if __name__ == "__main__":
    evaluate()
