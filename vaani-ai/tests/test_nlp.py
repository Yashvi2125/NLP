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
