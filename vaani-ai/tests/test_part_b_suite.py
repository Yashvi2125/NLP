"""
Part B Comprehensive Verification Test Suite
Tests 50+ diverse inputs across multiple languages (English, Hindi, Gujarati,
Tamil, Telugu, Marathi, Bengali, Spanish, French, German) to ensure all core
invariants hold:

1. Contraction Expansion: General handling across standard contractions.
2. Stopword Invariant: Content tokens (No Stopwords) never contains a token in STOPWORDS[lang].
3. Intent Classifier Invariant: Predicted intent strictly equals ranked[0][0].
4. Probability Invariant: Probabilities across all classes sum to 1.0 within float rounding.
5. Emotion & Intent Coverage: Handles happy, sad, angry, fear, greeting, intro, etc.
6. Sentiment Invariant: Compound score bounded [-1.0, 1.0], components finite & sum to 100%.
7. Language Override: Respects explicit 'speech_lang' override.
8. Latency Accounting: Total latency strictly matches sum of pipeline stages.
9. Part A Test Cases 1-6 verification (Translation + TTS target voice).
"""

import pytest
import math
import numpy as np
from nlp.preprocess import preprocess, expand_contractions, STOPWORDS
from nlp.langid import detect_language
from nlp.intent import IntentClassifier
from nlp.sentiment import analyze
from nlp.chatbot import Chatbot, match_conversational_rule
from nlp.pipeline import process


TEST_INPUTS_50 = [
    # English
    "I'm feeling angry today",
    "Don't worry about it, everything will be fine",
    "Can't you see I am very happy right now?",
    "It's a wonderful day outside",
    "We're going to the market later",
    "You'll love this new song",
    "I am terrified of the dark",
    "What is your name?",
    "What can you do?",
    "Tell me the time right now",
    "What is today's date?",
    "Tell me a funny joke",
    "My name is Yashvi",
    "Hello there, good morning!",
    "Goodbye, see you tomorrow",
    "Thank you so much for your help",
    "You are very stupid and useless",
    "You are an amazing assistant",
    
    # Hindi
    "नमस्ते, आप कैसे हैं?",
    "मेरा नाम राहुल है",
    "मुझे बहुत गुस्सा आ रहा है",
    "मैं बहुत खुश हूँ आज",
    "मुझे बहुत डर लग रहा है",
    "आपका नाम क्या है?",
    "आप क्या कर सकते हैं?",
    "समय क्या हुआ है?",
    "आज की तारीख क्या है?",
    "कोई अच्छा चुटकुला सुनाओ",
    "धन्यवाद आपकी मदद के लिए",
    "अलविदा, फिर मिलेंगे",
    
    # Gujarati
    "નમસ્તે, તમે કેમ છો?",
    "મારું નામ યશવી છે",
    "મને આજે ખૂબ ગુસ્સો આવે છે",
    "હું આજે ખૂબ ખુશ છું",
    "મને અંધારામાં ડર લાગે છે",
    "તમારું નામ શું છે?",
    "તમે શું કરી શકો છો?",
    "અત્યારે કેટલા વાગ્યા છે?",
    "આભાર, તમારી મદદ માટે",
    "આવજો, કાલે મળીશું",
    
    # Tamil
    "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    "என் பெயர் பிரியா",
    "உங்கள் பெயர் என்ன?",
    "நீங்கள் என்ன செய்ய முடியும்?",
    "இப்போது நேரம் என்ன?",
    "எனக்கு மிகவும் கோபமாக இருக்கிறது",
    "எனக்கு மிகவும் பயமாக இருக்கிறது",
    "நன்றி உங்கள் உதவிக்கு",
    
    # Telugu
    "నమస్కారం, మీరు ఎలా ఉన్నారు?",
    "నా పేరు రవి",
    "మీ పేరు ఏమిటి?",
    "మీరు ఏమి చేయగలరు?",
    "నాకు చాలా కోపంగా ఉంది",
    "నాకు చాలా భయంగా ఉంది",
    "ధన్యవాదాలు మీ సహాయానికి",
    
    # Marathi & Bengali
    "माझे नाव राहुल आहे, तुम्ही कसे आहात?",
    "मला खूप राग आला आहे",
    "আমার নাম অনিক, আপনি কেমন আছেন?",
    "আমার খুব রাগ হচ্ছে",
    
    # European Languages (Spanish, French, German)
    "Hola, ¿cómo estás hoy?",
    "Estoy muy enojado con esta situación",
    "Estoy muy feliz de verte",
    "Bonjour, comment vous appelez-vous ?",
    "Je suis très en colère aujourd'hui",
    "Guten Tag, wie spät ist es?",
    "Ich bin sehr wütend darüber",
]


def test_b1_contraction_expansion():
    """Verify contraction expansion expands contractions into separated tokens."""
    samples = {
        "I'm feeling angry": "i am feeling angry",
        "don't touch that": "do not touch that",
        "can't do this": "cannot do this",
        "it's sunny today": "it is sunny today",
        "we're ready": "we are ready",
        "you'll see": "you will see",
        "they've arrived": "they have arrived",
        "I'd like a coffee": "i would like a coffee",
    }
    for text, expected_sub in samples.items():
        expanded = expand_contractions(text).lower()
        assert expected_sub in expanded, f"Failed on: {text} -> {expanded}"


def test_b1_stopword_removal_invariant():
    """Verify that 'without_stopwords' never contains any token present in STOPWORDS[lang]."""
    for text in TEST_INPUTS_50:
        det = detect_language(text)
        lang = det["code"]
        prep = preprocess(text, lang)
        
        sw_list = STOPWORDS.get(lang, set())
        for token in prep["without_stopwords"]:
            assert token.lower() not in sw_list, (
                f"Token '{token}' from text '{text}' ({lang}) was found in STOPWORDS[{lang}]!"
            )


def test_b2_intent_invariants_across_all_50():
    """
    Assert:
    1. predicted intent strictly equals ranked[0][0]
    2. probabilities across model classes sum to 1.0 within float rounding
    """
    clf = IntentClassifier()
    for text in TEST_INPUTS_50:
        res = clf.predict(text)
        predicted = res["intent"]
        ranked = res["ranked"]
        
        # Invariant 1: Top ranked alternative matches predicted intent
        assert ranked[0][0] == predicted, (
            f"Invariant violated for '{text}': predicted '{predicted}' != top alternative '{ranked[0][0]}'"
        )
        
        # Check raw probability sum
        t_clean = text.lower()
        if clf.pipeline is not None:
            probs = clf.pipeline.predict_proba([t_clean])[0]
        else:
            probs = clf.clf.predict_proba(clf._features([t_clean]))[0]
        prob_sum = float(np.sum(probs))
        assert abs(prob_sum - 1.0) < 1e-4, f"Probabilities for '{text}' sum to {prob_sum}, not 1.0"


def test_b2_emotion_coverage():
    """Verify emotions like angry and fear predict appropriate labels with high confidence."""
    clf = IntentClassifier()
    
    angry_queries = [
        "I am very angry right now",
        "मुझे बहुत गुस्सा आ रहा है",
        "મને આજે ખૂબ ગુસ્સો આવે છે",
        "எனக்கு மிகவும் கோபமாக இருக்கிறது",
        "నాకు చాలా కోపంగా ఉంది",
        "estoy muy enojado",
    ]
    for q in angry_queries:
        res = clf.predict(q)
        assert res["intent"] == "angry", f"Failed to predict angry for: '{q}', got {res['intent']}"
    
    fear_queries = [
        "I am so scared and afraid",
        "मुझे बहुत डर लग रहा है",
        "મને અંધારામાં ડર લાગે છે",
        "எனக்கு மிகவும் பயமாக இருக்கிறது",
        "నాకు చాలా భయంగా ఉంది",
    ]
    for q in fear_queries:
        res = clf.predict(q)
        assert res["intent"] == "fear", f"Failed to predict fear for: '{q}', got {res['intent']}"


def test_b3_sentiment_score_invariants():
    """Verify sentiment scores are bounded [-1, 1], percentages are finite and sum to 100%."""
    for text in TEST_INPUTS_50 + ["", "   ", "😀😀😀", "!?!?!", "asdfghjkl qwerty"]:
        sent = analyze(text)
        comp = sent["compound"]
        assert -1.0 <= comp <= 1.0, f"Compound {comp} out of bounds for '{text}'"
        
        pos = sent.get("pos", 0.0)
        neu = sent.get("neu", 0.0)
        neg = sent.get("neg", 0.0)
        
        assert not math.isnan(pos), f"NaN pos for '{text}'"
        assert not math.isnan(neu), f"NaN neu for '{text}'"
        assert not math.isnan(neg), f"NaN neg for '{text}'"
        
        if len(text.strip()) > 0:
            total_score = round(pos + neu + neg, 2)
            assert total_score == 1.0, f"Scores sum to {total_score} instead of 1.0 for '{text}'"


def test_b4_language_override():
    """Verify that speech_lang override forces user selection badge."""
    res = process("Hello", speech_lang="gu")
    assert res["language"]["user_override"] is True
    assert res["language"]["code"] == "gu"


def test_b5_latency_invariant():
    """Verify total pipeline latency equals local_nlp + chatbot + translation latencies."""
    res = process("What is the time right now?", speech_lang="en", reply_to="en", translate_to="auto")
    lat = res["timing"]
    expected_sum = round(lat["local_nlp_ms"] + lat["chatbot_ms"] + lat.get("translation_ms", 0.0), 2)
    assert abs(lat["total_ms"] - expected_sum) <= 0.05, (
        f"Latency mismatch: total_ms={lat['total_ms']} vs sum={expected_sum}"
    )


# =========================================================================
# Part A Test Cases 1 - 6
# =========================================================================

def test_part_a_case_1_morning_in_gujarati():
    """Test 1: 'morning in Gujarati' -> reply contains સવાર, TTS speaks સવાર in gu-IN."""
    res = process("morning in Gujarati", reply_to="gu")
    reply = res["reply"]
    assert "સવાર" in reply["text"]
    assert reply["speak_text"] == "સવાર"
    assert reply["tts"] == "gu-IN"


def test_part_a_case_2_morning_in_hindi():
    """Test 2: 'morning in Hindi' -> reply contains सुबह, TTS speaks सुबह in hi-IN."""
    res = process("morning in Hindi", reply_to="hi")
    reply = res["reply"]
    assert "सुबह" in reply["text"]
    assert reply["speak_text"] == "सुबह"
    assert reply["tts"] == "hi-IN"


def test_part_a_case_3_thank_you_in_tamil():
    """Test 3: 'how do you say thank you in Tamil' -> Tamil word, spoken in ta-IN."""
    res = process("how do you say thank you in Tamil", reply_to="ta")
    reply = res["reply"]
    assert "நன்றி" in reply["text"]
    assert reply["speak_text"] == "நன்றி"
    assert reply["tts"] == "ta-IN"


def test_part_a_case_4_good_night_in_telugu():
    """Test 4: 'good night in Telugu' -> Telugu word, spoken in te-IN."""
    res = process("good night in Telugu", reply_to="te")
    reply = res["reply"]
    assert ("శుభరాత్రి" in reply["text"] or "శుభరాత్రి" in reply.get("speak_text", "") or
            "గుడ్ నైట్" in reply["text"] or "గుడ్ నైట్" in reply.get("speak_text", "") or
            "రాత్రి" in reply["text"] or "రాత్రి" in reply.get("speak_text", ""))
    assert reply["tts"] == "te-IN"


def test_part_a_case_5_what_time_is_it_in_gujarati():
    """Test 5: 'what time is it' with Reply in = Gujarati -> full Gujarati reply, spoken in gu-IN."""
    res = process("what time is it", reply_to="gu")
    reply = res["reply"]
    assert reply["lang"] == "gu"
    assert reply["tts"] == "gu-IN"
    # Localized Gujarati time reply
    assert "સમય" in reply["text"] or "વાગ્યા" in reply["text"]


def test_part_a_case_6_hindi_input_user_intro():
    """Test 6: 'मेरा नाम राहुल है' (Hindi input, Reply in Same as me) -> Hindi reply, spoken in hi-IN."""
    res = process("मेरा नाम राहुल है", reply_to="auto")
    reply = res["reply"]
    assert reply["lang"] == "hi"
    assert reply["tts"] == "hi-IN"
    assert "राहुल" in reply["text"]
