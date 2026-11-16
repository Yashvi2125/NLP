"""Conversational engine: intent -> response -> reply in the user's language."""
import random
from datetime import datetime

from .intent import IntentClassifier, extract_entities
from .translate import translate, PHRASEBOOK
from .languages import LANGUAGES, name_of
from .localized import LOCAL

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
    "fallback": ["Sorry, I didn't quite get that. You can ask me the time, a joke, or to translate a phrase."],
}

TRANSLATE_PHRASES = sorted(PHRASEBOOK, key=len, reverse=True)


class Chatbot:
    def __init__(self):
        self.clf = IntentClassifier().fit()

    def _handle_translate(self, text, entities, user_lang):
        target = next((e["value"] for e in entities if e["type"] == "LANGUAGE"), None)
        low = text.lower()
        phrase = next((p for p in TRANSLATE_PHRASES if p in low), None)
        if not target or target == "en" or not phrase:
            return "Tell me like this: “translate good morning to Hindi”.", "en"
        res = translate(phrase, "en", target)
        if not res["ok"]:
            return f"Sorry, I can't translate “{phrase}” to {name_of(target)} offline.", "en"
        return f"“{phrase}” in {name_of(target)} is: {res['text']}", "en"

    def respond(self, text: str, user_lang: str, target_lang: str, now=None, sentiment=None) -> dict:
        pred = self.clf.predict(text)
        entities = extract_entities(text)
        intent = pred["intent"]
        # Sentiment-aware disambiguation: "sad" vs "happy" share sentence structure, polarity separates them.
        if sentiment and intent in ("sad", "happy") and abs(sentiment["compound"]) >= 0.2:
            intent = "happy" if sentiment["compound"] > 0 else "sad"
            pred = {**pred, "intent": intent, "note": "intent refined by sentiment"}
        now = now or datetime.now()
        ents = {e["type"].lower(): e["value"] for e in entities}

        if intent == "translate_request":
            reply_en, src_lang = self._handle_translate(text, entities, user_lang)
            reply = reply_en
            engine = "rule"
            # translate-request answers are already in the target language; show in English frame
            return {**pred, "entities": entities, "reply": reply, "reply_en": reply_en, "reply_lang": "en", "engine": engine}

        templates = REPLIES.get(intent, REPLIES["fallback"])
        if intent == "user_intro":
            reply_en = templates[0].format(person=ents["person"]) if "person" in ents else templates[1]
        else:
            reply_en = random.choice(templates).format(time=now.strftime("%I:%M %p"),
                                                      date=now.strftime("%A, %d %B %Y"))
        if target_lang == "en":
            return {**pred, "entities": entities, "reply": reply_en, "reply_en": reply_en, "reply_lang": "en", "engine": "template"}

        key = "user_intro_noname" if intent == "user_intro" and "person" not in ents else intent
        local = LOCAL.get(key, {}).get(target_lang)
        if local:
            local = local.format(time=now.strftime("%I:%M %p"), date=now.strftime("%d-%m-%Y"),
                                 person=ents.get("person", ""))
            return {**pred, "entities": entities, "reply": local, "reply_en": reply_en, "reply_lang": target_lang, "engine": "offline localisation"}
        tr = translate(reply_en, "en", target_lang)
        return {**pred, "entities": entities, "reply": tr["text"], "reply_en": reply_en,
                "reply_lang": target_lang if tr["ok"] else "en", "engine": tr["engine"]}
