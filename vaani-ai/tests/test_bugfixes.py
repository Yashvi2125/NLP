"""Automated regression and unit test suite for Post-Phase 10 critical bugfixes.

Covers:
1. Gemini API diagnostics, failure categorization (missing key, auth error, model 404, rate limit, timeout, network error).
2. Multilingual conversational intent router (Tamil, Gujarati, Hindi, Marathi, Bengali, Hinglish, English).
3. Robust translation command parsing ("to", "in", fuzzy aliases, spelling errors, ambiguous commands).
4. Sentiment analysis finite score calculations (Tamil, Gujarati, empty, punctuation-only, emoji-only, zero-denominator guard, no NaN/Inf).
"""

import math
import json
import pytest
from unittest.mock import patch, MagicMock

import requests
from nlp.gemini_client import GeminiClient
from nlp.chatbot import Chatbot, resolve_target_language, match_conversational_rule
from nlp.sentiment import analyze
from nlp.translate import translate
from app import app


# =====================================================================
# 1. Gemini Client Tests (Mocked - Zero Quota Consumption)
# =====================================================================

def test_gemini_missing_api_key():
    client = GeminiClient(api_key="")
    assert not client.is_configured
    res = client.generate_chat([{"parts": [{"text": "Hello"}]}])
    assert res["ok"] is False
    assert res["reason"] == "missing_api_key"
    assert res["engine"] == "offline fallback"


@patch("requests.post")
def test_gemini_success_mocked(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "Sundar Pichai is the CEO of Google."}]},
            "finishReason": "STOP"
        }]
    }
    mock_post.return_value = mock_resp

    client = GeminiClient(api_key="AIzaSyFakeKeyForMockTesting123456789")
    assert client.is_configured
    res = client.generate_chat([{"parts": [{"text": "Who is the CEO of Google?"}]}])

    assert res["ok"] is True
    assert "Sundar Pichai" in res["text"]
    assert res["engine"] == "gemini hybrid"
    assert res["http_status"] == 200


@patch("requests.post")
def test_gemini_auth_error_mocked(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_post.return_value = mock_resp

    client = GeminiClient(api_key="AIzaSyInvalidKeyWithExpiredStatus999")
    res = client.generate_chat([{"parts": [{"text": "Hello"}]}])

    assert res["ok"] is False
    assert res["reason"] == "auth_error"
    assert res["http_status"] == 401
    assert res["engine"] == "offline fallback"


@patch("requests.post")
def test_gemini_model_not_found_fallback_mocked(mock_post):
    # First model returns 404, second model returns 200
    resp_404 = MagicMock()
    resp_404.status_code = 404

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Success on fallback model."}]}}]
    }

    mock_post.side_effect = [resp_404, resp_200]

    client = GeminiClient(api_key="AIzaSyFakeKeyForMockTesting123456789")
    res = client.generate_chat([{"parts": [{"text": "Hello"}]}])

    assert res["ok"] is True
    assert res["text"] == "Success on fallback model."
    assert mock_post.call_count == 2


@patch("requests.post")
def test_gemini_rate_limit_mocked(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_post.return_value = mock_resp

    client = GeminiClient(api_key="AIzaSyFakeKeyForMockTesting123456789")
    res = client.generate_chat([{"parts": [{"text": "Hello"}]}])

    assert res["ok"] is False
    assert res["reason"] == "rate_limited"
    assert res["http_status"] == 429


@patch("requests.post")
def test_gemini_timeout_mocked(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out after 8s")

    client = GeminiClient(api_key="AIzaSyFakeKeyForMockTesting123456789")
    res = client.generate_chat([{"parts": [{"text": "Hello"}]}])

    assert res["ok"] is False
    assert res["reason"] == "timeout"


def test_gemini_failure_triggers_offline_fallback():
    # Chatbot with unconfigured Gemini
    bot = Chatbot(gemini_api_key="")
    res = bot.respond("What is the distance to Mars?", "en", "en")
    assert res["engine"] == "offline fallback"
    assert "fallback_reason" in res
    assert res["reply"] is not None


# =====================================================================
# 2. Multilingual Conversational Queries (Tamil, Gujarati, Hindi, etc.)
# =====================================================================

def test_conversational_rule_matching():
    # Tamil
    assert match_conversational_rule("உங்கள் பெயர் என்ன") == "ask_name"
    assert match_conversational_rule("நீங்கள் என்ன செய்ய முடியும்") == "capabilities"
    assert match_conversational_rule("வணக்கம்") == "greeting"
    assert match_conversational_rule("எப்படி இருக்கிறீர்கள்") == "how_are_you"

    # Gujarati
    assert match_conversational_rule("તમારું નામ શું છે?") == "ask_name"
    assert match_conversational_rule("તમે શું કરી શકો?") == "capabilities"
    assert match_conversational_rule("તમે કેમ છો?") == "how_are_you"

    # Hindi
    assert match_conversational_rule("आपका नाम क्या है?") == "ask_name"
    assert match_conversational_rule("आप क्या कर सकते हैं?") == "capabilities"
    assert match_conversational_rule("आप कैसे हैं?") == "how_are_you"

    # Bengali & Marathi
    assert match_conversational_rule("আপনার নাম কী?") == "ask_name"
    assert match_conversational_rule("तुमचे नाव काय आहे?") == "ask_name"

    # Hinglish & English
    assert match_conversational_rule("aapka naam kya hai") == "ask_name"
    assert match_conversational_rule("What is your name?") == "ask_name"
    assert match_conversational_rule("what can you do") == "capabilities"
    assert match_conversational_rule("how are you") == "how_are_you"


def test_chatbot_multilingual_conversational_responses():
    bot = Chatbot(gemini_api_key="")

    # Tamil name query
    res_ta = bot.respond("உங்கள் பெயர் என்ன", "ta", "ta")
    assert res_ta["intent"] == "ask_name"
    assert "வாணி ஏஐ" in res_ta["reply"]
    assert res_ta["engine"] in ("offline localisation", "template (local)")

    # Gujarati name query
    res_gu = bot.respond("તમારું નામ શું છે?", "gu", "gu")
    assert res_gu["intent"] == "ask_name"
    assert "વાણી એઆઈ" in res_gu["reply"]

    # Hindi name query
    res_hi = bot.respond("आपका नाम क्या है?", "hi", "hi")
    assert res_hi["intent"] == "ask_name"
    assert "वाणी एआई" in res_hi["reply"]

    # English name query
    res_en = bot.respond("What is your name?", "en", "en")
    assert res_en["intent"] == "ask_name"
    assert "VaaniAI" in res_en["reply"]


# =====================================================================
# 3. Translation Command Parsing Tests
# =====================================================================

def test_resolve_target_language():
    # Exact
    assert resolve_target_language("Hindi") == "hi"
    assert resolve_target_language("gujarati") == "gu"
    assert resolve_target_language("Tamil") == "ta"
    assert resolve_target_language("ગુજરાતી") == "gu"

    # Typos (fuzzy matches)
    assert resolve_target_language("gujararti") == "gu"
    assert resolve_target_language("gujrati") == "gu"
    assert resolve_target_language("tamill") == "ta"
    assert resolve_target_language("bengli") == "bn"
    assert resolve_target_language("spanis") == "es"

    # Non-language vocabulary should NOT match
    assert resolve_target_language("eating") is None
    assert resolve_target_language("morning") is None
    assert resolve_target_language("car") is None


def test_translation_command_patterns():
    bot = Chatbot(gemini_api_key="")

    # "to" and "in"
    res1 = bot.respond("translate good morning to Hindi", "en", "en")
    assert "सुप्रभात" in res1["reply"]

    res2 = bot.respond("translate good morning in Hindi", "en", "en")
    assert "सुप्रभात" in res2["reply"]

    # Spelling error: "gujararti"
    res3 = bot.respond("translate i'm eating in gujararti", "en", "en")
    assert "હું" in res3["reply"] and "Gujarati" in res3["reply"]

    # Standard languages
    res4 = bot.respond("translate hello to Gujarati", "en", "en")
    assert "નમસ્તે" in res4["reply"]

    res5 = bot.respond("translate how are you in Tamil", "en", "en")
    assert "நீங்கள் எப்படி இருக்கிறீர்கள்" in res5["reply"]

    # Ambiguous commands guide the user politely
    res_ambig = bot.respond("translate please", "en", "en")
    assert "Tell me like this:" in res_ambig["reply"]


# =====================================================================
# 4. Sentiment Analysis NaN Bug Tests
# =====================================================================

def test_sentiment_no_nan_tamil():
    # Text with zero sentiment tokens from user screenshot
    s = analyze("உங்கள் பெயர் என்ன", "ta")
    assert not math.isnan(s["compound"])
    assert not math.isnan(s["confidence"])
    assert not math.isnan(s["pos"])
    assert not math.isnan(s["neu"])
    assert not math.isnan(s["neg"])
    assert s["pos"] == 0.0
    assert s["neu"] == 1.0
    assert s["neg"] == 0.0
    assert round(s["pos"] + s["neu"] + s["neg"], 2) == 1.0


def test_sentiment_no_nan_gujarati():
    s = analyze("તમારું નામ શું છે?", "gu")
    assert not math.isnan(s["compound"])
    assert s["neu"] == 1.0
    assert s["pos"] == 0.0
    assert s["neg"] == 0.0


def test_sentiment_empty_and_punctuation():
    # Empty
    s_empty = analyze("", "en")
    assert s_empty["compound"] == 0.0
    assert s_empty["neu"] == 1.0
    assert not math.isnan(s_empty["pos"])

    # Punctuation only
    s_punct = analyze("! ? . , : ; ... ---", "en")
    assert not math.isnan(s_punct["compound"])
    assert not math.isnan(s_punct["neu"])

    # Whitespace only
    s_space = analyze("   \n\t   ", "hi")
    assert not math.isnan(s_space["compound"])
    assert s_space["neu"] == 1.0


def test_sentiment_emojis():
    # Emoji positive
    s_pos = analyze("😀 ❤️ 🎉", "ta")
    assert s_pos["compound"] > 0
    assert s_pos["label"] == "positive"
    assert not math.isnan(s_pos["pos"])

    # Emoji negative
    s_neg = analyze("😡 😭 💔", "hi")
    assert s_neg["compound"] < 0
    assert s_neg["label"] == "negative"
    assert not math.isnan(s_neg["neg"])


def test_api_responses_never_contain_nan():
    client = app.test_client()

    # Test analyze endpoint with Tamil text
    resp = client.post("/api/analyze", json={"text": "உங்கள் பெயர் என்ன", "lang": "ta"})
    assert resp.status_code == 200
    raw_text = resp.get_data(as_text=True)
    assert "NaN" not in raw_text
    assert "Infinity" not in raw_text

    data = resp.get_json()
    s = data["sentiment"]
    assert isinstance(s["pos"], (int, float))
    assert isinstance(s["neu"], (int, float))
    assert isinstance(s["neg"], (int, float))
    assert not math.isnan(s["pos"])
    assert not math.isnan(s["neu"])
    assert not math.isnan(s["neg"])

    # Test analyze endpoint with Gujarati text
    resp_chat = client.post("/api/analyze", json={"text": "તમારું નામ શું છે?", "reply_to": "gu"})
    assert resp_chat.status_code == 200
    raw_chat = resp_chat.get_data(as_text=True)
    assert "NaN" not in raw_chat
    assert "Infinity" not in raw_chat


# =====================================================================
# 5. Multilingual Translation & Pronoun Context Tests
# =====================================================================

def test_translation_dutch_full_sentence():
    bot = Chatbot()
    res = bot.respond("The CEO of Google is Sundar Pichai translate it to dutch", "en", "en")
    assert res["intent"] == "translate_request"
    assert "Dutch" in res["reply"]
    assert "Sundar Pichai" in res["reply"]


def test_translation_french_typo_no_keyword():
    bot = Chatbot()
    res = bot.respond("good morning in frenh", "en", "en")
    assert res["intent"] == "translate_request"
    assert "French" in res["reply"]
    assert "bonjour" in res["reply"].lower()


def test_translation_hindi_typo_no_keyword():
    bot = Chatbot()
    res = bot.respond("good afternoon in hindu", "en", "en")
    assert res["intent"] == "translate_request"
    assert "Hindi" in res["reply"]
    assert "शुभ दोपहर" in res["reply"]


def test_translation_gujarati_afternoon():
    bot = Chatbot()
    res = bot.respond("good afternoon in gujarati", "en", "en")
    assert res["intent"] == "translate_request"
    assert "Gujarati" in res["reply"]
    assert "શુભ બપોર" in res["reply"]


def test_translation_morning_evening_phrasebook():
    bot = Chatbot()
    res_m = bot.respond("morning in gujarati", "en", "en")
    assert res_m["intent"] == "translate_request"
    assert "સવાર" in res_m["reply"]

    res_e = bot.respond("evening in gujarati", "en", "en")
    assert res_e["intent"] == "translate_request"
    assert "સાંજ" in res_e["reply"]


def test_translation_gemini_datacenter_fallback():
    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("Blocked on cloud IP")), \
         patch("deep_translator.MyMemoryTranslator.translate", side_effect=Exception("Rate limited on cloud IP")), \
         patch.object(GeminiClient, "generate_chat") as mock_gemini:
        mock_gemini.return_value = {
            "ok": True,
            "text": "કૃત્રિમ બુદ્ધિમત્તા",
            "engine": "gemini (online)",
        }
        res = translate("Artificial intelligence", "en", "gu")
        assert res["ok"] is True
        assert res["engine"] == "gemini (online)"
        assert res["text"] == "કૃત્રિમ બુદ્ધિમત્તા"


def test_translation_pronoun_context():
    bot = Chatbot()
    import uuid
    sid = str(uuid.uuid4())
    # Turn 1
    bot.respond("The CEO of Google is Sundar Pichai.", "en", "en", session_id=sid)
    # Turn 2: refers to 'it'
    res = bot.respond("translate it to dutch", "en", "en", session_id=sid)
    assert res["intent"] == "translate_request"
    assert "Dutch" in res["reply"]
    assert "Sundar Pichai" in res["reply"]


@patch.object(GeminiClient, "generate_chat")
def test_gemini_multilingual_reply_routing(mock_gen):
    mock_gen.return_value = {
        "ok": True,
        "text": "અમદાવાદ ગુજરાત રાજ્યમાં આવેલું છે.",
        "engine": "gemini hybrid",
        "model": "gemini-2.5-flash",
        "latency_ms": 350.0,
        "http_status": 200,
    }
    bot = Chatbot()
    res = bot.respond("ahmedabad is located in which state", "en", "gu")
    assert res["reply_lang"] == "gu"
    assert "અમદાવાદ" in res["reply"]
    # Check that lang_code='gu' was passed to generate_chat
    assert mock_gen.call_args[1]["lang_code"] == "gu"

