"""Conversational engine: intent -> response -> reply in the user's language.

Hybrid Architecture:
1. Local Multilingual Intent Router: High-confidence commands (time, date, joke, alarm, translation)
   and basic conversational intents (name, capabilities, greetings, how are you) in Tamil, Gujarati,
   Hindi, Marathi, Bengali, Hinglish, and English handled locally and instantly (< 2 ms) with zero quota.
2. Gemini API Fallback: Open-ended questions, general knowledge, and unhandled queries routed
   to Google Gemini with multi-turn conversational context memory.
3. Offline Graceful Fallback: When Gemini is unavailable (network down, rate limited, missing key, timeout),
   cleanly falls back to localized offline responses without crashing.
4. Multi-Turn Session Memory: Preserves session context, entities, and resolves conversational references.
"""

import re
import time
import random
import difflib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from .intent import IntentClassifier, extract_entities, CONFIDENCE_THRESHOLD
from .translate import translate
from .languages import LANGUAGES, name_of
from .localized import LOCAL
from .memory import get_memory_manager, SessionMemory
from .gemini_client import GeminiClient
from .langid import detect_language

logger = logging.getLogger("vaani.chatbot")

# English reply templates (the source of truth). Localised offline copies live in LOCAL.
REPLIES = {
    "greeting": ["Hello! I'm VaaniAI. Speak or type in any supported language and I'll understand you."],
    "goodbye": ["Goodbye! Have a wonderful day."],
    "thanks": ["You're welcome! Happy to help."],
    "ask_time": ["The current time is {time}."],
    "ask_date": ["Today is {date}."],
    "ask_name": ["I'm VaaniAI, a multilingual voice assistant built with NLP."],
    "user_intro": ["Nice to meet you, {person}!", "Nice to meet you!"],
    "capabilities": ["I can transcribe your speech, detect your language, translate, analyse sentiment and chat with you."],
    "how_are_you": ["I'm doing great, thank you for asking! How can I help you today?",
                    "I'm functioning well and ready to assist you! How are you doing?"],
    "joke": ["Why did the NLP model go to therapy? It had too many unresolved dependencies!",
             "I told my computer I needed a break, and it said: no problem, I'll go to sleep."],
    "sad": ["I'm sorry you're feeling this way. I'm here to listen. Do you want to talk about it?"],
    "angry": ["I hear your frustration. Take a deep breath. How can I help resolve this?"],
    "fear": ["Don't worry, you are safe. Take a slow breath. I am here to help you."],
    "happy": ["That's wonderful to hear! Keep smiling."],
    "about_project": ["VaaniAI is an NLP project combining speech-to-text, language detection, translation, sentiment analysis and an intent-based chatbot."],
    "weather": ["I can't check live weather in this offline-friendly version, but a weather API can be plugged in easily."],
    "compliment": ["Thank you, that's very kind!"],
    "alarm_set": ["I have set your alarm. Alarm features are simulated in this offline-friendly demo."],
    "alarm_query": ["You have no active alarms set at the moment."],
    "music": ["Playing music is simulated in this version. You can connect a music streaming API."],
    "qa_factoid": ["That is a great question! I'm ready to help you with factual information."],
    "fallback": ["Sorry, I didn't quite get that. You can ask me the time, a joke, or to translate a phrase."],
}

# Canonical language lookup dictionary for translation commands
LANGUAGE_CANONICAL = {
    "english": "en", "en": "en", "angrezi": "en",
    "hindi": "hi", "hi": "hi", "हिन्दी": "hi", "हिंदी": "hi", "hindu": "hi",
    "marathi": "mr", "mr": "mr", "मराठी": "mr",
    "gujarati": "gu", "gu": "gu", "ગુજરાતી": "gu", "gujrati": "gu", "gujararti": "gu",
    "bengali": "bn", "bn": "bn", "বাংলা": "bn", "bangla": "bn",
    "tamil": "ta", "ta": "ta", "தமிழ்": "ta", "tamizh": "ta",
    "telugu": "te", "te": "te", "తెలుగు": "te",
    "urdu": "ur", "ur": "ur", "اردو": "ur",
    "spanish": "es", "es": "es", "español": "es", "spanis": "es",
    "french": "fr", "fr": "fr", "français": "fr", "frenh": "fr", "franch": "fr",
    "german": "de", "de": "de", "deutsch": "de",
    "italian": "it", "it": "it", "italiano": "it",
    "portuguese": "pt", "pt": "pt", "português": "pt",
    "dutch": "nl", "nl": "nl", "nederlands": "nl", "holland": "nl",
    "russian": "ru", "ru": "ru", "русский": "ru",
    "arabic": "ar", "ar": "ar", "العربية": "ar",
    "japanese": "ja", "ja": "ja", "日本語": "ja",
    "chinese": "zh", "zh": "zh", "中文": "zh",
    "korean": "ko", "ko": "ko", "한국어": "ko",
    "hinglish": "hinglish",
}

# Language-aware conversational intent patterns for instant local response
CONVERSATIONAL_RULES = [
    ("ask_name", [
        # Tamil
        r"உங்கள்\s+பெயர்\s+என்ன", r"உன்\s+பெயர்\s+என்ன", r"நீ\s+யார்", r"யார்\s+நீ",
        # Gujarati
        r"તમારું\s+નામ\s+શું\s+છે", r"તારું\s+નામ\s+શું\s+છે", r"તમે\s+કોણ\s+છો", r"કોણ\s+છો\s+તમે",
        # Hindi
        r"आपका\s+नाम\s+क्या\s+है", r"तुम्हारा\s+नाम\s+क्या\s+है", r"तुम\s+कौन\s+हो", r"आप\s+कौन\s+हैं",
        # Marathi
        r"तुमचे\s+नाव\s+काय\s+आहे", r"तुझे\s+नाव\s+काय\s+आहे", r"तुम्ही\s+कोण\s+आहात", r"तू\s+कोण\s+आहेस",
        # Bengali
        r"আপনার\s+নাম\s+কী", r"আপনার\s+নাম\s+কি", r"তোমার\s+নাম\s+কি", r"আপনি\s+কে", r"তুমি\s+কে",
        # Hinglish
        r"\b(?:aapka|tumhara|tera)\s+naam\s+kya\s+hai\b", r"\b(?:who\s+are\s+you|aap\s+kaun\s+ho)\b",
        # English
        r"\bwhat\s+is\s+your\s+name\b", r"\bwhat['’]?s\s+your\s+name\b", r"\bwho\s+are\s+you\b",
    ]),
    ("capabilities", [
        # Tamil
        r"நீங்கள்\s+என்ன\s+செய்ய\s+முடியும்", r"உன்னால்\s+என்ன\s+செய்ய\s+முடியும்", r"என்ன\s+செய்ய\s+முடியும்",
        # Gujarati
        r"તમે\s+શું\s+કરી\s+શકો", r"તમે\s+શું\s+કામ\s+કરી\s+શકો",
        # Hindi
        r"आप\s+क्या\s+कर\s+सकते\s+हैं", r"तुम\s+क्या\s+कर\s+सकते\s+हो", r"क्या\s+कर\s+सकते\s+हो",
        # Marathi
        r"तुम्ही\s+काय\s+करू\s+शकता", r"तू\s+काय\s+करू\s+शकतोस",
        # Bengali
        r"আপনি\s+কী\s+করতে\s+পারেন", r"তুমি\s+কি\s+করতে\s+পারো",
        # Hinglish
        r"\b(?:aap|tum)\s+kya\s+kar\s+sakte\s+ho\b", r"\bkya\s+kya\s+kar\s+sakte\s+ho\b",
        # English
        r"\bwhat\s+can\s+you\s+do\b", r"\bhow\s+can\s+you\s+help(?:\s+me)?\b", r"\bwhat\s+are\s+your\s+capabilities\b",
    ]),
    ("how_are_you", [
        # Tamil
        r"நீங்கள்\s+எப்படி\s+இருக்கிறீர்கள்", r"எப்படி\s+இருக்கிறீர்கள்", r"எப்படி\s+இருக்கீங்க", r"\bநலமா\b",
        # Gujarati
        r"તમે\s+કેમ\s+છો", r"\bકેમ\s+છો\b", r"\bમજામાં\b",
        # Hindi
        r"आप\s+कैसे\s+हैं", r"तुम\s+कैसे\s+हो", r"कैसा\s+चल\s+रहा\s+है", r"\bकैसे\s+हो\b",
        # Marathi
        r"तुम्ही\s+कसे\s+आहात", r"तू\s+कसा\s+आहेस", r"\bकसे\s+आहात\b",
        # Bengali
        r"আপনি\s+কেমন\s+আছেন", r"তুমি\s+কেমন\s+আছো", r"\bকেমন\s+আছেন\b",
        # Hinglish
        r"\b(?:aap|tum)\s+kaise\s+ho\b", r"\bkaise\s+ho\b", r"\bhow\s+are\s+you\b", r"\bhow\s+r\s+u\b",
        # English
        r"\bhow\s+are\s+you(?:\s+doing)?\b", r"\bhow['’]?s\s+it\s+going\b", r"\bhow\s+do\s+you\s+do\b",
    ]),
    ("greeting", [
        # Tamil
        r"வணக்கம்",
        # Gujarati
        r"નમસ્તે", r"નમસ્કાર", r"પ્રણામ",
        # Hindi
        r"नमस्ते", r"नमस्कार", r"प्रणाम",
        # Marathi
        r"नमस्कार",
        # Bengali
        r"নমস্কার", r"সালাম",
        # Hinglish
        r"\b(?:namaste|namaskar|pranam|hello|hi|hey)\b",
        # English
        r"\b(?:hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening)\b",
    ]),
    ("goodbye", [
        r"\b(?:bye|goodbye|see\s+you|alvida|aavjo)\b",
        r"போய்\s+வருகிறேன்", r"বিদায়", r"આવજો",
    ]),
    ("thanks", [
        r"\b(?:thank\s+you|thanks|dhanyavad|shukriya|aabhar)\b",
        r"நன்றி", r"ধন্যবাদ", r"આભાર",
    ]),
]


def resolve_target_language(raw_lang: str) -> Optional[str]:
    """Resolve target language name/alias with conservative fuzzy typo correction."""
    if not raw_lang:
        return None
    w = raw_lang.strip().lower()
    w = re.sub(r"[?!.,।:;\"'“”]+", "", w).strip()
    if not w:
        return None

    # 1. Exact match in canonical map (including 2-letter codes)
    if w in LANGUAGE_CANONICAL:
        return LANGUAGE_CANONICAL[w]

    # 2. Check against full LANGUAGES registry names
    for code, info in LANGUAGES.items():
        if w == code or w == info.get("name", "").lower():
            return code

    # 3. Conservative fuzzy matching: ONLY against names with length >= 4
    # This prevents short vocabulary words (e.g. 'car', 'bar', 'war') from matching 2-letter codes like 'ar'
    full_candidates = [k for k in LANGUAGE_CANONICAL.keys() if len(k) >= 4]
    matches = difflib.get_close_matches(w, full_candidates, n=1, cutoff=0.80)
    if matches:
        return LANGUAGE_CANONICAL[matches[0]]

    return None


def match_conversational_rule(text: str) -> Optional[str]:
    """Match basic conversational intents across supported languages."""
    clean = re.sub(r"[?!.,।:;\"'“”]+", " ", text).strip().lower()
    tokens = clean.split()
    if not tokens:
        return None

    # Never intercept translation queries as conversational rules
    if "translate" in clean:
        return None
    trailing_lang_match = re.search(r"\b(?:in|to|into)\s+([A-Za-z\u0900-\u0DFF]+)[.?!]*$", text, flags=re.IGNORECASE)
    if trailing_lang_match and resolve_target_language(trailing_lang_match.group(1)):
        return None

    # Priority 1: Specific queries (name, capabilities, how_are_you)
    for intent in ("ask_name", "capabilities", "how_are_you"):
        patterns = next(p for i, p in CONVERSATIONAL_RULES if i == intent)
        for pat in patterns:
            if re.search(pat, text, flags=re.IGNORECASE | re.UNICODE) or re.search(pat, clean, flags=re.IGNORECASE | re.UNICODE):
                return intent

    # Priority 2: Standalone greetings / thanks / goodbye
    # Only match if there are no explicit command words (time, date, translate, weather, joke, alarm, music)
    command_keywords = {"time", "date", "clock", "translate", "weather", "joke", "alarm", "song", "music", "play", "call", "samay", "tarikh", "vaqt", "நேரம்", "தேதி", "समय", "तारीख"}
    has_command_keyword = any(k in clean for k in command_keywords)

    if not has_command_keyword:
        for intent in ("greeting", "goodbye", "thanks"):
            patterns = next(p for i, p in CONVERSATIONAL_RULES if i == intent)
            for pat in patterns:
                if re.search(pat, text, flags=re.IGNORECASE | re.UNICODE) or re.search(pat, clean, flags=re.IGNORECASE | re.UNICODE):
                    return intent

    return None


class Chatbot:
    """Hybrid conversational chatbot combining local classifier with Gemini API fallback and session memory."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.clf = IntentClassifier()
        if not self.clf.fitted:
            self.clf.fit()
        self.memory = get_memory_manager()
        self.gemini = GeminiClient(api_key=gemini_api_key)

    def _handle_translate(self, text: str, entities: list, user_lang: str, session: Optional[SessionMemory] = None) -> Tuple[str, str]:
        """Robust parser for translation commands accepting 'to', 'in', typos, and arbitrary phrases."""
        clean_text = text.strip()

        phrase = None
        target_code = None

        # Pattern 0: <phrase> translate (it/this/that) to/in/into <lang>
        # e.g., "The CEO of Google is Sundar Pichai translate it to dutch"
        m0 = re.search(
            r"^(?P<phrase>.+?)\s+(?:please\s+)?translate(?:\s+(?:it|this|that|the\s+above))?\s+(?:to|in|into)\s+(?P<lang>[A-Za-z\u0900-\u0DFF]+)[.?!]*$",
            clean_text,
            flags=re.IGNORECASE | re.UNICODE,
        )
        if m0:
            cand_code = resolve_target_language(m0.group("lang"))
            if cand_code:
                phrase = m0.group("phrase").strip()
                target_code = cand_code

        # Pattern 1: translate <phrase> to/in/into <lang>
        # e.g., "translate good morning to Hindi", "translate i'm eating in gujararti"
        if not target_code:
            m1 = re.search(
                r"^(?:please\s+)?translate\s+[\"\'“”]?(?P<phrase>.+?)[\"\'“”]?\s+(?:to|in|into)\s+(?P<lang>[A-Za-z\u0900-\u0DFF]+)[.?!]*$",
                clean_text,
                flags=re.IGNORECASE | re.UNICODE,
            )
            if m1:
                cand_code = resolve_target_language(m1.group("lang"))
                if cand_code:
                    phrase = m1.group("phrase").strip()
                    target_code = cand_code

        # Pattern 2: translate to/in/into <lang>: <phrase>
        if not target_code:
            m2 = re.search(
                r"^(?:please\s+)?translate\s+(?:to|in|into)\s+(?P<lang>[A-Za-z\u0900-\u0DFF]+)[:\s]+[\"\'“”]?(?P<phrase>.+?)[\"\'“”]*[.?!]*$",
                clean_text,
                flags=re.IGNORECASE | re.UNICODE,
            )
            if m2:
                cand_code = resolve_target_language(m2.group("lang"))
                if cand_code:
                    phrase = m2.group("phrase").strip()
                    target_code = cand_code

        # Pattern 3: how to say/what is <phrase> in <lang>
        if not target_code:
            m3 = re.search(
                r"^(?:how\s+(?:to|do\s+you)\s+say|what\s+is)\s+[\"\'“”]?(?P<phrase>.+?)[\"\'“”]?\s+in\s+(?P<lang>[A-Za-z\u0900-\u0DFF]+)[.?!]*$",
                clean_text,
                flags=re.IGNORECASE | re.UNICODE,
            )
            if m3:
                cand_code = resolve_target_language(m3.group("lang"))
                if cand_code:
                    phrase = m3.group("phrase").strip()
                    target_code = cand_code

        # Pattern 4: <phrase> in/to/into <lang>
        # e.g., "good morning in frenh", "good afternoon in hindu", "good morning in gujarati"
        if not target_code:
            m4 = re.search(
                r"^[\"\'“”]?(?P<phrase>[^?]+?)[\"\'“”]?\s+(?:in|to|into)\s+(?P<lang>[A-Za-z\u0900-\u0DFF]+)[.?!]*$",
                clean_text,
                flags=re.IGNORECASE | re.UNICODE,
            )
            if m4:
                cand_code = resolve_target_language(m4.group("lang"))
                if cand_code:
                    phrase = m4.group("phrase").strip()
                    target_code = cand_code

        # Fallback: check entities for LANGUAGE
        if not target_code:
            target_ent = next((e["value"] for e in entities if e["type"] == "LANGUAGE"), None)
            if target_ent and target_ent != "en":
                target_code = target_ent
                # Try to extract phrase before the language or preposition
                m_sub = re.search(r"translate\s+[\"\'“”]?(.*?)(?:to|in|into|$)", clean_text, flags=re.IGNORECASE)
                if m_sub and m_sub.group(1).strip():
                    phrase = m_sub.group(1).strip()

        # Clean extracted phrase
        if phrase:
            phrase = re.sub(r"^[\"\'“”]+|[\"\'“”]+$", "", phrase).strip()

        # Pronoun / conversational memory resolution: "translate it to dutch"
        if phrase and phrase.lower() in ("it", "this", "that", "the above") and session and session.turns:
            for turn in reversed(session.turns):
                t_val = (turn.text or "").strip()
                if t_val and t_val.lower() != clean_text.lower() and not t_val.lower().startswith("translate "):
                    phrase = t_val
                    break

        # If phrase or target language is missing or ambiguous, guide user clearly
        if not target_code or not phrase:
            guide = "Tell me like this: “translate <phrase> to <language>” (e.g., “translate good morning to Hindi” or “translate hello in Gujarati”)."
            return {"display": guide, "speak_text": guide, "speak_lang": "en", "speak_tts": "en-IN"}

        # Execute translation using multi-tier engine
        res = translate(phrase, "auto", target_code)
        target_name = name_of(target_code)
        target_tts = LANGUAGES.get(target_code, {}).get("tts", "en-IN")
        if res.get("ok") and res.get("text"):
            display_text = f"“{phrase}” in {target_name} is: {res['text']}"
            return {
                "display": display_text,
                "speak_text": res["text"],
                "speak_lang": target_code,
                "speak_tts": target_tts,
            }
        fail_msg = f"Sorry, I couldn't translate “{phrase}” to {target_name} right now."
        return {"display": fail_msg, "speak_text": fail_msg, "speak_lang": "en", "speak_tts": "en-IN"}

    def respond(self, text: str, user_lang: str, target_lang: str, now=None, sentiment=None, session_id: Optional[str] = None) -> dict:
        """Route message through local intent engine or Gemini fallback using multi-turn session memory."""
        t_start = time.perf_counter()
        clean_text = (text or "").strip()

        # -----------------------------------------------------------------
        # Step 0: Check Multilingual Conversational Rules
        # -----------------------------------------------------------------
        matched_rule_intent = match_conversational_rule(clean_text)
        if matched_rule_intent:
            intent = matched_rule_intent
            confidence = 0.99
            pred = {"intent": intent, "confidence": 0.99, "ranked": [[intent, 0.99]], "rule_override": True}
        else:
            pred = self.clf.predict(clean_text)
            intent = pred["intent"]
            confidence = pred["confidence"]

        entities = extract_entities(clean_text, user_lang)

        # Check for translation command patterns
        trailing_m = re.search(r"\b(?:in|to|into)\s+([A-Za-z\u0900-\u0DFF]+)[.?!]*$", clean_text, flags=re.IGNORECASE)
        is_trailing_lang = bool(trailing_m and resolve_target_language(trailing_m.group(1)))
        if "translate" in clean_text.lower() or is_trailing_lang:
            intent = "translate_request"
            confidence = 0.99
            pred = {**pred, "intent": intent, "confidence": 0.99}

        # Sentiment-aware disambiguation: "sad" vs "happy" share sentence structure, polarity separates them.
        if sentiment and intent in ("sad", "happy") and abs(sentiment.get("compound", 0.0)) >= 0.2:
            intent = "happy" if sentiment["compound"] > 0 else "sad"
            pred = {**pred, "intent": intent, "note": "intent refined by sentiment"}

        now = now or datetime.now()
        ents = {e["type"].lower(): e["value"] for e in entities}

        # Retrieve or initialize isolated session memory
        session = self.memory.get_or_create(session_id)
        session.add_turn("user", clean_text, lang=user_lang, entities=entities, intent=intent)

        # -----------------------------------------------------------------
        # 1. High-Confidence Local Intent Routing (Fast-Path, Offline)
        # -----------------------------------------------------------------
        is_local_command = (
            intent == "translate_request"
            or (
                intent not in ("fallback", "qa_factoid")
                and (confidence >= CONFIDENCE_THRESHOLD or matched_rule_intent is not None)
                and (intent in REPLIES or intent in LOCAL)
            )
        )

        if is_local_command:
            # Special command: translation
            if intent == "translate_request":
                tr_info = self._handle_translate(clean_text, entities, user_lang, session=session)
                reply_display = tr_info["display"]
                session.add_turn("model", reply_display, lang="en")
                return {
                    **pred,
                    "entities": entities,
                    "reply": reply_display,
                    "reply_en": reply_display,
                    "reply_lang": "en",
                    "speak_text": tr_info.get("speak_text", reply_display),
                    "speak_tts": tr_info.get("speak_tts", "en-IN"),
                    "engine": "rule",
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                    "session_id": session.session_id,
                }

            # Local template formatting
            templates = REPLIES.get(intent, REPLIES["fallback"])
            person_name = ents.get("person") or session.get_last_entity("person")

            if intent == "user_intro":
                reply_en = templates[0].format(person=person_name) if person_name else templates[1]
            elif intent in ("ask_time", "ask_date"):
                reply_en = random.choice(templates).format(
                    time=now.strftime("%I:%M %p"),
                    date=now.strftime("%A, %d %B %Y"),
                )
            else:
                reply_en = random.choice(templates)

            # Determine response language: prefer target_lang, fallback to user_lang
            effective_lang = target_lang if target_lang != "auto" else user_lang
            if effective_lang == "en" and target_lang == "en":
                session.add_turn("model", reply_en, lang="en")
                return {
                    **pred,
                    "entities": entities,
                    "reply": reply_en,
                    "reply_en": reply_en,
                    "reply_lang": "en",
                    "engine": "template (local)",
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                    "session_id": session.session_id,
                }

            # Offline localized response for target/user language
            key = "user_intro_noname" if intent == "user_intro" and not person_name else intent
            local_template = LOCAL.get(key, {}).get(effective_lang) or LOCAL.get(key, {}).get(user_lang)

            if local_template:
                local_reply = local_template.format(
                    time=now.strftime("%I:%M %p"),
                    date=now.strftime("%d-%m-%Y"),
                    person=person_name or "",
                )
                session.add_turn("model", local_reply, lang=effective_lang)
                return {
                    **pred,
                    "entities": entities,
                    "reply": local_reply,
                    "reply_en": reply_en,
                    "reply_lang": effective_lang,
                    "engine": "offline localisation",
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                    "session_id": session.session_id,
                }

            # If English was requested or no localized template exists
            if effective_lang == "en":
                session.add_turn("model", reply_en, lang="en")
                return {
                    **pred,
                    "entities": entities,
                    "reply": reply_en,
                    "reply_en": reply_en,
                    "reply_lang": "en",
                    "engine": "template (local)",
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                    "session_id": session.session_id,
                }

            # Fallback to translate English template to requested target language
            tr = translate(reply_en, "en", effective_lang)
            final_reply = tr["text"] if tr["ok"] else reply_en
            final_lang = effective_lang if tr["ok"] else "en"
            session.add_turn("model", final_reply, lang=final_lang)
            return {
                **pred,
                "entities": entities,
                "reply": final_reply,
                "reply_en": reply_en,
                "reply_lang": final_lang,
                "engine": tr.get("engine", "rule"),
                "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                "session_id": session.session_id,
            }

        # -----------------------------------------------------------------
        # 2. Gemini API Fallback (Open-ended, General Knowledge, Low Conf)
        # -----------------------------------------------------------------
        gemini_reason = "not_configured"
        gemini_status = None
        effective_lang = target_lang if target_lang != "auto" else user_lang

        if self.gemini.is_configured:
            gemini_contents = session.get_gemini_contents()
            logger.info("Routing query to Gemini API fallback (%s) in lang=%s", self.gemini.model, effective_lang)
            gemini_res = self.gemini.generate_chat(
                gemini_contents,
                lang_code=effective_lang,
                context_entities=session.context_entities,
            )

            if gemini_res["ok"]:
                reply_text = gemini_res["text"]
                final_lang = effective_lang

                # Safety check: If user requested a non-English language but Gemini returned English text, translate it
                if effective_lang != "en":
                    det_rep = detect_language(reply_text)
                    if det_rep.get("code") == "en" and effective_lang not in ("en", "hinglish"):
                        tr_safe = translate(reply_text, "en", effective_lang)
                        if tr_safe.get("ok") and tr_safe.get("text"):
                            reply_text = tr_safe["text"]

                session.add_turn("model", reply_text, lang=final_lang)
                final_intent = "open_ended" if intent in ("fallback", "qa_factoid") else intent
                ranked_out = [[final_intent, r[1]] if idx == 0 else r for idx, r in enumerate(pred.get("ranked", []))]
                return {
                    **pred,
                    "intent": final_intent,
                    "ranked": ranked_out,
                    "entities": entities,
                    "reply": reply_text,
                    "reply_en": reply_text,
                    "reply_lang": final_lang,
                    "engine": gemini_res["engine"],
                    "latency_ms": gemini_res.get("latency_ms"),
                    "model": gemini_res.get("model"),
                    "session_id": session.session_id,
                }
            else:
                gemini_reason = gemini_res.get("reason", "unknown_failure")
                gemini_status = gemini_res.get("http_status")
                logger.warning("Gemini API call failed (%s, status: %s). Falling back to offline engine.", gemini_reason, gemini_status)
        else:
            logger.warning("Gemini API key is not configured. Falling back to offline engine.")

        # -----------------------------------------------------------------
        # 3. Graceful Offline Fallback (Network down, missing key, timeout)
        # -----------------------------------------------------------------
        fallback_templates = REPLIES["fallback"]
        reply_en = random.choice(fallback_templates)
        effective_lang = target_lang if target_lang != "auto" else user_lang

        if effective_lang != "en":
            local = LOCAL.get("fallback", {}).get(effective_lang) or LOCAL.get("fallback", {}).get(user_lang)
            if local:
                reply = local
                rep_lang = effective_lang
            else:
                tr = translate(reply_en, "en", effective_lang)
                reply = tr["text"] if tr["ok"] else reply_en
                rep_lang = effective_lang if tr["ok"] else "en"
        else:
            reply = reply_en
            rep_lang = "en"

        session.add_turn("model", reply, lang=rep_lang)
        return {
            **pred,
            "entities": entities,
            "reply": reply,
            "reply_en": reply_en,
            "reply_lang": rep_lang,
            "engine": "offline fallback",
            "fallback_reason": gemini_reason,
            "fallback_http_status": gemini_status,
            "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
            "session_id": session.session_id,
        }
