"""Conversational engine: intent -> response -> reply in the user's language.

Hybrid Architecture:
1. Local Intent Router: High-confidence commands (alarm, time, date, joke, music, weather, greeting, etc.)
   handled locally and instantly (< 2 ms) with zero quota or network overhead.
2. Gemini API Fallback: Open-ended questions, fallback intents, and low-confidence queries (< 0.45 threshold)
   routed to Google Gemini with multi-turn conversational context memory.
3. Offline Graceful Fallback: When offline, rate-limited, or unconfigured, falls back cleanly to local responses.
4. Multi-Turn Session Memory: Preserves session context, entities, and resolves pronouns.
"""

import random
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from .intent import IntentClassifier, extract_entities, CONFIDENCE_THRESHOLD
from .translate import translate, PHRASEBOOK
from .languages import LANGUAGES, name_of
from .localized import LOCAL
from .memory import get_memory_manager, SessionMemory
from .gemini_client import GeminiClient

# English reply templates (the source of truth). Localised offline copies live in LOCAL below.
REPLIES = {
    "greeting": ["Hello! I'm VaaniAI. Speak or type in any supported language and I'll understand you."],
    "goodbye": ["Goodbye! Have a wonderful day."],
    "thanks": ["You're welcome! Happy to help."],
    "ask_time": ["The current time is {time}."],
    "ask_date": ["Today is {date}."],
    "ask_name": ["I'm VaaniAI, a multilingual voice assistant built with NLP."],
    "user_intro": ["Nice to meet you, {person}!", "Nice to meet you!"],
    "capabilities": ["I can transcribe your speech, detect your language, translate, analyse sentiment and chat with you."],
    "joke": ["Why did the NLP model go to therapy? It had too many unresolved dependencies!",
             "I told my computer I needed a break, and it said: no problem, I'll go to sleep."],
    "sad": ["I'm sorry you're feeling this way. I'm here to listen. Do you want to talk about it?"],
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

TRANSLATE_PHRASES = sorted(PHRASEBOOK, key=len, reverse=True)


class Chatbot:
    """Hybrid conversational chatbot combining local classifier with Gemini API fallback and session memory."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.clf = IntentClassifier()
        if not self.clf.fitted:
            self.clf.fit()
        self.memory = get_memory_manager()
        self.gemini = GeminiClient(api_key=gemini_api_key)

    def _handle_translate(self, text: str, entities: list, user_lang: str):
        target = next((e["value"] for e in entities if e["type"] == "LANGUAGE"), None)
        low = text.lower()
        phrase = next((p for p in TRANSLATE_PHRASES if p in low), None)
        if not target or target == "en" or not phrase:
            return "Tell me like this: “translate good morning to Hindi”.", "en"
        res = translate(phrase, "en", target)
        if not res["ok"]:
            return f"Sorry, I can't translate “{phrase}” to {name_of(target)} offline.", "en"
        return f"“{phrase}” in {name_of(target)} is: {res['text']}", "en"

    def respond(self, text: str, user_lang: str, target_lang: str, now=None, sentiment=None, session_id: Optional[str] = None) -> dict:
        """Route message through local intent engine or Gemini fallback using multi-turn session memory."""
        t_start = time.perf_counter()
        pred = self.clf.predict(text)
        entities = extract_entities(text, user_lang)
        intent = pred["intent"]
        confidence = pred["confidence"]

        # Sentiment-aware disambiguation: "sad" vs "happy" share sentence structure, polarity separates them.
        if sentiment and intent in ("sad", "happy") and abs(sentiment["compound"]) >= 0.2:
            intent = "happy" if sentiment["compound"] > 0 else "sad"
            pred = {**pred, "intent": intent, "note": "intent refined by sentiment"}

        now = now or datetime.now()
        ents = {e["type"].lower(): e["value"] for e in entities}

        # Retrieve or initialize isolated session memory
        session = self.memory.get_or_create(session_id)
        session.add_turn("user", text, lang=user_lang, entities=entities, intent=intent)

        # -----------------------------------------------------------------
        # 1. High-Confidence Local Intent Routing (Fast-Path, Offline)
        # -----------------------------------------------------------------
        is_local_command = (
            intent == "translate_request"
            or (
                intent not in ("fallback", "qa_factoid")
                and confidence >= CONFIDENCE_THRESHOLD
                and intent in REPLIES
            )
        )

        if is_local_command:
            # Special command: translation
            if intent == "translate_request":
                reply_en, src_lang = self._handle_translate(text, entities, user_lang)
                session.add_turn("model", reply_en, lang="en")
                return {
                    **pred,
                    "entities": entities,
                    "reply": reply_en,
                    "reply_en": reply_en,
                    "reply_lang": "en",
                    "engine": "rule",
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                    "session_id": session.session_id,
                }

            # Local template formatting
            templates = REPLIES.get(intent, REPLIES["fallback"])
            person_name = ents.get("person") or session.get_last_entity("person")

            if intent == "user_intro":
                reply_en = templates[0].format(person=person_name) if person_name else templates[1]
            else:
                reply_en = random.choice(templates).format(
                    time=now.strftime("%I:%M %p"),
                    date=now.strftime("%A, %d %B %Y"),
                )

            # English response
            if target_lang == "en":
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

            # Offline localized response if available
            key = "user_intro_noname" if intent == "user_intro" and not person_name else intent
            local = LOCAL.get(key, {}).get(target_lang)
            if local:
                local_reply = local.format(
                    time=now.strftime("%I:%M %p"),
                    date=now.strftime("%d-%m-%Y"),
                    person=person_name or "",
                )
                session.add_turn("model", local_reply, lang=target_lang)
                return {
                    **pred,
                    "entities": entities,
                    "reply": local_reply,
                    "reply_en": reply_en,
                    "reply_lang": target_lang,
                    "engine": "offline localisation",
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                    "session_id": session.session_id,
                }

            # Local translation fallback
            tr = translate(reply_en, "en", target_lang)
            final_reply = tr["text"] if tr["ok"] else reply_en
            final_lang = target_lang if tr["ok"] else "en"
            session.add_turn("model", final_reply, lang=final_lang)
            return {
                **pred,
                "entities": entities,
                "reply": final_reply,
                "reply_en": reply_en,
                "reply_lang": final_lang,
                "engine": tr["engine"],
                "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                "session_id": session.session_id,
            }

        # -----------------------------------------------------------------
        # 2. Gemini API Fallback (Open-ended, General Knowledge, Low Conf)
        # -----------------------------------------------------------------
        if self.gemini.is_configured:
            gemini_contents = session.get_gemini_contents()
            gemini_res = self.gemini.generate_chat(
                gemini_contents,
                lang_code=user_lang,
                context_entities=session.context_entities,
            )

            if gemini_res["ok"]:
                reply_text = gemini_res["text"]
                session.add_turn("model", reply_text, lang=user_lang)
                return {
                    **pred,
                    "intent": "open_ended" if intent in ("fallback", "qa_factoid") else intent,
                    "entities": entities,
                    "reply": reply_text,
                    "reply_en": reply_text,
                    "reply_lang": user_lang,
                    "engine": gemini_res["engine"],
                    "latency_ms": gemini_res.get("latency_ms"),
                    "model": gemini_res.get("model"),
                    "session_id": session.session_id,
                }

        # -----------------------------------------------------------------
        # 3. Graceful Offline Fallback (Network down, missing key, timeout)
        # -----------------------------------------------------------------
        fallback_templates = REPLIES["fallback"]
        reply_en = random.choice(fallback_templates)

        if target_lang != "en":
            local = LOCAL.get("fallback", {}).get(target_lang)
            if local:
                reply = local
                engine = "offline fallback"
                rep_lang = target_lang
            else:
                tr = translate(reply_en, "en", target_lang)
                reply = tr["text"] if tr["ok"] else reply_en
                engine = "offline fallback"
                rep_lang = target_lang if tr["ok"] else "en"
        else:
            reply = reply_en
            engine = "offline fallback"
            rep_lang = "en"

        session.add_turn("model", reply, lang=rep_lang)
        return {
            **pred,
            "entities": entities,
            "reply": reply,
            "reply_en": reply_en,
            "reply_lang": rep_lang,
            "engine": engine,
            "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
            "session_id": session.session_id,
        }
