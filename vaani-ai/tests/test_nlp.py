import pytest
from nlp.preprocess import preprocess, tokenize, stem
from nlp.langid import detect_language
from nlp.sentiment import analyze
from nlp.intent import extract_entities
from nlp.translate import translate
from nlp.pipeline import process, get_bot


def test_preprocess_hindi_keeps_matras():
    r = preprocess("मेरा नाम राहुल है", "hi")
    assert r["tokens"] == ["मेरा", "नाम", "राहुल", "है"]
    assert "है" not in r["without_stopwords"]


def test_preprocess_english_pipeline():
    r = preprocess("I am running quickly! https://x.com 😀", "en")
    assert r["normalized"] == "I am running quickly!"
    assert r["stems"] == ["run", "quick"]


def test_stem_short_words_untouched():
    assert stem("is") == "is" and stem("walking") == "walk"


@pytest.mark.parametrize("text,code", [
    ("Hello, how are you doing today?", "en"), ("नमस्ते आप कैसे हैं", "hi"), ("Hola, ¿cómo estás hoy?", "es"),
    ("Bonjour, comment allez-vous ?", "fr"), ("Guten Morgen, wie geht es dir?", "de"),
    ("mera naam Yashvi hai aur main theek hoon", "hinglish"), ("તમે કેમ છો", "gu"),
    ("வணக்கம் எப்படி இருக்கிறீர்கள்", "ta"), ("আপনি কেমন আছেন", "bn"), ("तुम्ही कसे आहात, मी ठीक आहे", "mr"),
    ("Ciao, come stai oggi?", "it"), ("Olá, tudo bem?", "pt"), ("Hallo, hoe gaat het?", "nl"),
    ("Привет, как дела?", "ru"), ("مرحبا، كيف حالك؟", "ar"), ("こんにちは、お元気ですか？", "ja"),
    ("你好，今天天气怎么样？", "zh"), ("안녕하세요, 반갑습니다", "ko"), ("నమస్కారం, ఎలా ఉన్నారు?", "te"),
    ("آپ کیسے ہیں؟", "ur"),
])
def test_language_detection(text, code):
    assert detect_language(text)["code"] == code


def test_sentiment_english():
    assert analyze("I love this, it is wonderful!", "en")["label"] == "positive"
    assert analyze("This is terrible and I hate it", "en")["label"] == "negative"


def test_sentiment_offline_lexicon_non_english():
    assert analyze("मैं बहुत उदास हूँ", "hi")["label"] in ("negative", "neutral")  # offline lexicon path


def test_entities():
    e = {(x["type"], x["value"]) for x in extract_entities("My name is Aarav, call 9876543210 at 5:30 pm in Pune")}
    assert ("PERSON", "Aarav") in e and ("CITY", "Pune") in e and ("PHONE", "9876543210") in e
    assert ("TIME", "5:30 pm") in e


def test_entities_hindi_name():
    assert ("PERSON", "राहुल") in {(x["type"], x["value"]) for x in extract_entities("मेरा नाम राहुल है")}


def test_translate_offline_phrasebook_or_online():
    r = translate("good morning", "en", "hi")
    assert r["ok"] and r["text"]
    back = translate("धन्यवाद", "hi", "en")
    assert back["ok"] and "thank" in back["text"].lower()


def test_translate_identity():
    assert translate("hello", "en", "en")["engine"] == "identity"


# Held-out utterances (not in the training file) -> realistic accuracy check
HELD_OUT = [
    ("hey, how's everything", "greeting"), ("thank you so much for that", "thanks"),
    ("what's the time now", "ask_time"), ("tell me a funny joke", "joke"),
    ("bye, see you soon", "goodbye"), ("what can you do for me", "capabilities"),
    ("translate hello to french", "translate_request"), ("नमस्ते", "greeting"),
    ("धन्यवाद दोस्त", "thanks"), ("अलविदा", "goodbye"), ("hola", "greeting"), ("merci beaucoup", "thanks"),
    ("what is today's date", "ask_date"), ("who made this project", "about_project"),
]


def test_intent_heldout_accuracy():
    bot = get_bot()
    hits = sum(bot.clf.predict(t)["intent"] == i for t, i in HELD_OUT)
    assert hits / len(HELD_OUT) >= 0.8, f"{hits}/{len(HELD_OUT)}"


def test_low_confidence_falls_back():
    assert get_bot().clf.predict("zxqv blorp wug")["intent"] == "fallback"


def test_pipeline_end_to_end_hindi_reply():
    r = process("नमस्ते", reply_to="auto")
    assert r["language"]["code"] == "hi" and r["intent"]["name"] == "greeting"
    assert r["reply"]["lang"] == "hi" and r["reply"]["text"]


def test_pipeline_sentiment_refines_sad_happy():
    assert process("I am so happy today, life is wonderful!")["intent"]["name"] == "happy"
    assert process("I feel terrible and sad")["intent"]["name"] == "sad"


def test_pipeline_empty():
    assert "error" in process("   ")


# ---------------- Phase 2: Enhanced NLP Preprocessing Tests ----------------

def test_preprocess_preserves_original_text():
    raw = "  Hello,   This Is A TEST!  "
    r = preprocess(raw, "en")
    assert r["original"] == raw
    assert r["normalized"] == "Hello, This Is A TEST!"


def test_preprocess_unicode_dandas_and_combining_marks():
    hindi_text = "नमस्ते। आज मौसम बहुत अच्छा है॥"
    r = preprocess(hindi_text, "hi")
    assert r["original"] == hindi_text
    assert "।" not in r["normalized"] and "॥" not in r["normalized"]
    assert "मौसम" in r["tokens"] and "अच्छा" in r["tokens"]
    # Stopword 'है' removed
    assert "है" not in r["without_stopwords"]


def test_preprocess_gujarati_stopwords_and_matras():
    gu_text = "આજની તારીખ શું છે?"
    r = preprocess(gu_text, "gu")
    assert "તારીખ" in r["tokens"]
    assert "છે" not in r["without_stopwords"]
    assert "શું" not in r["without_stopwords"]
    # Matras preserved
    assert "તારીખ" in r["without_stopwords"]


def test_preprocess_marathi_stopwords_and_inflections():
    mr_text = "आज किती वाजले आहेत?"
    r = preprocess(mr_text, "mr")
    assert "वाजले" in r["tokens"]
    assert "आहेत" not in r["without_stopwords"]
    # 'वाजले' preserved without destructive stem truncation to 'वाज'
    assert "वाजले" in r["stems"]


def test_preprocess_hinglish_elongation_and_normalization():
    r = preprocess("booohoooot dhanyavaaaaad bhai", "hinglish")
    assert "bahut" in r["tokens"]
    assert "dhanyavad" in r["tokens"]
    assert "bhai" in r["tokens"]


def test_preprocess_hinglish_guards_english_and_names():
    r = preprocess("Please tell Rahul the time", "hinglish")
    # English keywords and proper names MUST NOT be transformed
    assert "please" in r["tokens"]
    assert "tell" in r["tokens"]
    assert "rahul" in r["tokens"]
    assert "time" in r["tokens"]


def test_preprocess_mixed_language_detection():
    r1 = preprocess("Today का weather kaisa hai?", "hi")
    assert r1["is_mixed"] is True
    assert "latin" in r1["active_scripts"] and "devanagari" in r1["active_scripts"]

    r2 = preprocess("What is the time right now?", "en")
    assert r2["is_mixed"] is False
    assert r2["active_scripts"] == ["latin"]


def test_preprocess_empty_and_short_inputs():
    assert preprocess("", "en")["tokens"] == []
    assert preprocess("a", "en")["tokens"] == ["a"]
    assert preprocess("?", "en")["tokens"] == []


# -------------------------------------------------------------
# Phase 4: Multilingual Sentiment Analysis Unit Tests
# -------------------------------------------------------------

@pytest.mark.parametrize("text,lang,expected_label", [
    # English (VADER)
    ("I love this assistant, it is wonderful!", "en", "positive"),
    ("This is a terrible and awful mistake.", "en", "negative"),
    ("The train leaves at 5:30 pm today.", "en", "neutral"),
    ("This is not good at all.", "en", "negative"),
    # Hindi (Lexicon + bidirectional negation + emoji)
    ("यह बहुत अच्छा और सुंदर है।", "hi", "positive"),
    ("मुझे बहुत बुरा और दुखद लगा।", "hi", "negative"),
    ("आज बहुत उदास हूँ 😭", "hi", "negative"),
    ("यह काम बिल्कुल अच्छा नहीं है।", "hi", "negative"),
    ("आज शुक्रवार है।", "hi", "neutral"),
    # Marathi
    ("हा प्रकल्प अतिशय छान आणि सुंदर आहे.", "mr", "positive"),
    ("मला फार वाईट आणि दुःख झाले.", "mr", "negative"),
    ("हे मला मुळीच आवडले नाही.", "mr", "negative"),
    ("उद्या सकाळी सात वाजता गजर लावा.", "mr", "neutral"),
    # Gujarati
    ("આ ખૂબ સરસ અને સુંદર છે.", "gu", "positive"),
    ("મને બહુ ખરાબ અને દુઃખ લાગ્યું.", "gu", "negative"),
    ("આ સારું નથી.", "gu", "negative"),
    # Hinglish
    ("aaj main bohot khush aur excited hoon!", "hinglish", "positive"),
    ("yeh bohot bekar aur ghatiya tha yaar", "hinglish", "negative"),
    ("yeh bilkul acha nahi hai", "hinglish", "negative"),
    # Bengali & Tamil
    ("এটি খুব ভালো এবং সুন্দর হয়েছে।", "bn", "positive"),
    ("আমার খুব খারাপ লাগছে এবং কষ্ট হচ্ছে।", "bn", "negative"),
    ("இது மிகவும் நல்ல மற்றும் அழகான ஒன்று.", "ta", "positive"),
    ("எனக்கு மிகவும் மோசமான மற்றும் கவலையான நாள்.", "ta", "negative"),
    # European Languages (es, fr, de, it, pt, nl, ru)
    ("¡Me encanta este lugar, es maravilloso y genial!", "es", "positive"),
    ("Esto no es bueno.", "es", "negative"),
    ("C'est vraiment magnifique, j'adore et c'est génial !", "fr", "positive"),
    ("Ce n'est pas bon du tout.", "fr", "negative"),
    ("Das ist wirklich wunderbar, fantastisch und super!", "de", "positive"),
    ("Das ist nicht gut.", "de", "negative"),
    ("Questo posto è bellissimo, meraviglioso e ottimo!", "it", "positive"),
    ("Isso é maravilhoso, muito bom e excelente!", "pt", "positive"),
    ("Dit is echt geweldig, mooi en uitstekend!", "nl", "positive"),
    ("Это действительно прекрасно, отлично и замечательно!", "ru", "positive"),
    # Arabic, Urdu, Telugu
    ("هذا رائع جدا وجميل وممتاز!", "ar", "positive"),
    ("یہ بہت اچھا اور خوبصورت ہے۔", "ur", "positive"),
    ("ఇది చాలా మంచి మరియు అద్భుతంగా ఉంది.", "te", "positive"),
    # East Asian Languages (ja, zh, ko)
    ("これは本当に素晴らしい、最高で嬉しいです！", "ja", "positive"),
    ("これは最悪で、酷くて悲しいです。", "ja", "negative"),
    ("这太棒了，非常优秀，我很开心！", "zh", "positive"),
    ("这太糟糕了，非常差，很难过。", "zh", "negative"),
    ("이것은 정말 훌륭하고 최고로 행복합니다!", "ko", "positive"),
    ("이것은 최악이고 끔찍하며 슬픕니다.", "ko", "negative"),
])
def test_multilingual_sentiment_classification(text, lang, expected_label):
    res = analyze(text, lang)
    assert res["label"] == expected_label
    assert "compound" in res
    assert "confidence" in res
    assert "scores" in res
    assert "method" in res
    assert "support_tier" in res
    assert res["confidence"] > 0.6


def test_sentiment_emoji_valence():
    res_pos = analyze("Awesome job 🎉❤️", "en")
    assert res_pos["label"] == "positive"
    assert res_pos["scores"]["emoji"] > 0

    res_neg = analyze("I failed the test 😭💔", "en")
    assert res_neg["label"] == "negative"
    assert res_neg["scores"]["emoji"] < 0


def test_sentiment_empty_input():
    res = analyze("", "en")
    assert res["label"] == "neutral"
    assert res["compound"] == 0.0
    assert res["method"] == "empty"


# -------------------------------------------------------------
# Phase 5: Multilingual Named Entity Recognition (NER) Unit Tests
# -------------------------------------------------------------

def test_ner_multilingual_person_extraction():
    # English full name & famous icon
    e_en = {(x["type"], x["value"]) for x in extract_entities("My name is Albert Einstein and I live in Princeton")}
    assert ("PERSON", "Albert Einstein") in e_en

    # Hindi intro with trailing copula stripping
    e_hi = {(x["type"], x["value"]) for x in extract_entities("मेरा नाम राहुल शर्मा है")}
    assert ("PERSON", "राहुल शर्मा") in e_hi

    # Marathi intro
    e_mr = {(x["type"], x["value"]) for x in extract_entities("माझे नाव सचिन तेंदुलकर आहे")}
    assert ("PERSON", "सचिन तेंदुलकर") in e_mr

    # Gujarati intro
    e_gu = {(x["type"], x["value"]) for x in extract_entities("મારું નામ નરેન્દ્ર મોદી છે")}
    assert ("PERSON", "નરેન્દ્ર મોદી") in e_gu

    # Bengali intro
    e_bn = {(x["type"], x["value"]) for x in extract_entities("আমার নাম রবীন্দ্রনাথ ঠাকুর")}
    assert ("PERSON", "রবীন্দ্রনাথ ঠাকুর") in e_bn

    # Spanish intro
    e_es = {(x["type"], x["value"]) for x in extract_entities("Me llamo Carlos Santana")}
    assert ("PERSON", "Carlos Santana") in e_es

    # French intro
    e_fr = {(x["type"], x["value"]) for x in extract_entities("Je m'appelle Marie Curie")}
    assert ("PERSON", "Marie Curie") in e_fr

    # Russian intro
    e_ru = {(x["type"], x["value"]) for x in extract_entities("Меня зовут Владимир Путин")}
    assert ("PERSON", "Владимир Путин") in e_ru

    # Chinese intro
    e_zh = {(x["type"], x["value"]) for x in extract_entities("我叫李小龙，我是工程师")}
    assert ("PERSON", "李小龙") in e_zh

    # Japanese intro
    e_ja = {(x["type"], x["value"]) for x in extract_entities("私の名前は田中太郎です")}
    assert ("PERSON", "田中太郎") in e_ja


def test_ner_multilingual_locations_and_multiword():
    # Multi-word city
    e1 = {(x["type"], x["value"]) for x in extract_entities("Flight booked to New Delhi")}
    assert ("LOCATION", "New Delhi") in e1

    # Indic script city
    e2 = {(x["type"], x["value"]) for x in extract_entities("હું અમદાવાદ જાઉં છું")}
    assert ("LOCATION", "અમદાવાદ") in e2

    # Russian inflection ("в Москве")
    e3 = {(x["type"], x["value"]) for x in extract_entities("Я живу в Москве")}
    assert ("LOCATION", "москве") in e3 or any(x["type"] == "LOCATION" for x in extract_entities("Я живу в Москве"))

    # CJK city
    e4 = {(x["type"], x["value"]) for x in extract_entities("私は東京に行きます")}
    assert ("LOCATION", "東京") in e4


def test_ner_organizations_multilingual():
    # Global Tech and Indian Orgs
    e = {(x["type"], x["value"]) for x in extract_entities("Google and ISRO partnered with Tata Motors Ltd. today")}
    assert ("ORGANIZATION", "GOOGLE") in e or ("ORGANIZATION", "Google") in e
    assert ("ORGANIZATION", "ISRO") in e
    assert any(x["type"] == "ORGANIZATION" and "Tata" in x["value"] for x in extract_entities("Google and ISRO partnered with Tata Motors Ltd. today"))

    # Script-native organizations
    e_hi = {(x["type"], x["value"]) for x in extract_entities("इसरो ने नया मिशन शुरू किया")}
    assert ("ORGANIZATION", "इसरो") in e_hi


def test_ner_relative_dates_and_times():
    # Relative dates across scripts
    assert any(x["type"] == "DATE" for x in extract_entities("कल मिलेंगे", "hi"))
    assert any(x["type"] == "DATE" for x in extract_entities("उद्या भेटू", "mr"))
    assert any(x["type"] == "DATE" for x in extract_entities("આજે મીટિંગ છે", "gu"))
    assert any(x["type"] == "DATE" for x in extract_entities("Aujourd'hui à Paris", "fr"))
    assert any(x["type"] == "DATE" for x in extract_entities("Wir treffen uns morgen", "de"))
    assert any(x["type"] == "DATE" for x in extract_entities("今日は晴れです", "ja"))

    # Relative times
    assert any(x["type"] == "TIME" for x in extract_entities("कल सुबह आना", "hi"))
    assert any(x["type"] == "TIME" for x in extract_entities("સવારે મળીએ", "gu"))


def test_ner_monetary_values():
    # Rupee symbol and Indian words
    e1 = [x["value"] for x in extract_entities("फीस ₹500 है और डोनेशन ५०० करोड़ रुपये है")]
    assert any("₹500" in v or "५०० करोड़ रुपये" in v for v in e1)

    # Dollar and Euro
    e2 = [x["value"] for x in extract_entities("Price is 100 dollars or 50 euros")]
    assert any("100 dollars" in v for v in e2)
    assert any("50 euros" in v for v in e2)


def test_ner_phone_and_email_extraction():
    e = {(x["type"], x["value"]) for x in extract_entities("Reach us at contact@vaani.ai or +91 9876543210")}
    assert ("EMAIL", "contact@vaani.ai") in e
    assert ("PHONE", "+91 9876543210") in e


def test_ner_false_positive_guard():
    # Common conversational words must NOT be recognized as PERSON
    e1 = extract_entities("I am very happy and fine today")
    assert not any(x["type"] == "PERSON" for x in e1)

    e2 = extract_entities("Call me back later please")
    assert not any(x["type"] == "PERSON" for x in e2)

    e3 = extract_entities("मैं बहुत अच्छा हूँ")
    assert not any(x["type"] == "PERSON" for x in e3)



