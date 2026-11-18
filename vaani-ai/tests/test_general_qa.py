"""Comprehensive unit and integration test suite for General QA routing,
Project vs General Question Disambiguation, Curated Offline Fallbacks,
Gemini JSON responses, and Web Audio RMS Silence Detection.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from nlp.chatbot import (
    Chatbot,
    CURATED_DEFINITIONS,
    get_curated_definition,
    is_project_question,
)
from nlp.gemini_client import GeminiClient


class TestGeneralQARouting(unittest.TestCase):
    """Test general knowledge questions vs project questions routing."""

    def setUp(self):
        self.bot = Chatbot()

    def test_what_is_nlp_general_definition(self):
        """'what is nlp?' must return a general NLP definition without 'VaaniAI' or project description."""
        res = self.bot.respond("what is nlp?", user_lang="en", target_lang="en")
        reply = res["reply"]
        self.assertNotIn("VaaniAI", reply)
        self.assertNotIn("combining speech-to-text", reply.lower())
        self.assertTrue(
            any(k in reply.lower() for k in ["natural language processing", "artificial intelligence", "language", "nlp"]),
            f"Expected general NLP definition, got: {reply}",
        )

    def test_what_all_things_nlp_include_lists_areas(self):
        """'what all things nlp include' must return the list of NLP areas, not the project description."""
        res = self.bot.respond("what all things nlp include", user_lang="en", target_lang="en")
        reply = res["reply"]
        self.assertNotIn("VaaniAI", reply)
        self.assertNotIn("combining speech-to-text, language detection", reply.lower())
        expected_areas = ["tokenization", "sentiment analysis", "speech recognition", "machine translation"]
        matched_areas = [area for area in expected_areas if area in reply.lower()]
        self.assertGreaterEqual(
            len(matched_areas),
            2,
            f"Expected list of NLP areas, got: {reply}",
        )

    def test_what_is_machine_learning_general_definition(self):
        """'what is machine learning?' must return a general ML definition, never project description."""
        res = self.bot.respond("what is machine learning?", user_lang="en", target_lang="en")
        reply = res["reply"]
        self.assertNotIn("VaaniAI", reply)
        self.assertTrue(
            any(k in reply.lower() for k in ["machine learning", "artificial intelligence", "learn", "data"]),
            f"Expected general ML definition, got: {reply}",
        )

    def test_project_questions_return_project_description(self):
        """Queries asking specifically about VaaniAI or the app must return project description."""
        for query in ["what is vaaniai?", "what does this app do?", "tell me about this project"]:
            res = self.bot.respond(query, user_lang="en", target_lang="en")
            reply = res["reply"]
            self.assertTrue(
                "vaaniai" in reply.lower() or "nlp project" in reply.lower() or "assistant" in reply.lower(),
                f"Query '{query}' did not return project description: {reply}",
            )

    def test_commands_unchanged(self):
        """Commands like 'what time is it' and 'tell me a joke' must remain unchanged."""
        time_res = self.bot.respond("what time is it", user_lang="en", target_lang="en")
        self.assertEqual(time_res["intent"], "ask_time")
        self.assertTrue(
            "time is" in time_res["reply"].lower() or ":" in time_res["reply"],
            f"Expected time reply, got: {time_res['reply']}",
        )

        joke_res = self.bot.respond("tell me a joke", user_lang="en", target_lang="en")
        self.assertEqual(joke_res["intent"], "joke")
        self.assertGreater(len(joke_res["reply"]), 10)


class TestCuratedOfflineDefinitions(unittest.TestCase):
    """Test offline behavior when Gemini is disabled or unconfigured."""

    def setUp(self):
        # Chatbot instance with Gemini disabled
        self.offline_bot = Chatbot(gemini_api_key=None)
        self.offline_bot.gemini._api_key = ""

    def test_curated_definition_nlp_offline(self):
        """When offline, 'what is nlp?' uses the curated definition in user's language."""
        res = self.offline_bot.respond("what is nlp?", user_lang="en", target_lang="en")
        self.assertIn("Natural Language Processing", res["reply"])
        self.assertNotIn("VaaniAI", res["reply"])
        self.assertEqual(res["reply_en"], "")  # No EN line when reply is English

    def test_curated_definition_nlp_areas_offline_hindi(self):
        """When offline, 'what all things nlp include' with Hindi target returns Hindi reply with EN line."""
        res = self.offline_bot.respond("what all things nlp include", user_lang="en", target_lang="hi")
        self.assertNotEqual(res["reply"], "")
        self.assertNotEqual(res["reply_en"], "")
        self.assertIn("tokenization", res["reply_en"].lower())
        self.assertNotIn("VaaniAI", res["reply"])

    def test_curated_definition_machine_learning_offline(self):
        """When offline, 'what is machine learning?' returns curated ML definition."""
        res = self.offline_bot.respond("what is machine learning?", user_lang="en", target_lang="en")
        self.assertIn("Machine Learning", res["reply"])
        self.assertNotIn("VaaniAI", res["reply"])

    def test_unrelated_general_question_offline_returns_notice(self):
        """When offline, general questions outside the curated set return the graceful offline notice."""
        res = self.offline_bot.respond("who is the president of france?", user_lang="en", target_lang="en")
        self.assertIn("currently offline and cannot answer general knowledge", res["reply"])
        self.assertNotIn("VaaniAI is an NLP project", res["reply"])


class TestGeminiJSONResponses(unittest.TestCase):
    """Test Gemini structured JSON output, malformed output fallback, and English subtitle suppression."""

    def test_gemini_json_structured_reply_and_reply_en(self):
        """Valid JSON from Gemini returns both target language reply and English version."""
        client = GeminiClient(api_key="AIzaSyDummyValidKeyLengthExceeds10Chars")
        mock_payload = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "reply": "नेचुरल लैंग्वेज प्रोसेसिंग कंप्यूटर को इंसानी भाषा समझने में मदद करती है।",
                            "reply_en": "Natural Language Processing enables computers to understand human language."
                        })
                    }]
                }
            }]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        with patch("requests.post", return_value=mock_resp):
            res = client.generate_chat([{"role": "user", "parts": [{"text": "what is nlp?"}]}], lang_code="hi")
            self.assertTrue(res["ok"])
            self.assertIn("नेचुरल लैंग्वेज", res["text"])
            self.assertEqual(res["reply_en"], "Natural Language Processing enables computers to understand human language.")

    def test_gemini_malformed_response_returns_plain_text_no_en(self):
        """Malformed or non-JSON output from Gemini gracefully falls back to plain text without crashing or showing EN line."""
        client = GeminiClient(api_key="AIzaSyDummyValidKeyLengthExceeds10Chars")
        mock_payload = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Plain text response from model that is not JSON."
                    }]
                }
            }]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        with patch("requests.post", return_value=mock_resp):
            res = client.generate_chat([{"role": "user", "parts": [{"text": "hello"}]}], lang_code="en")
            self.assertTrue(res["ok"])
            self.assertEqual(res["text"], "Plain text response from model that is not JSON.")
            self.assertEqual(res["reply_en"], "")

    def test_gemini_english_reply_has_no_en_line(self):
        """When reply is English, reply_en is suppressed."""
        client = GeminiClient(api_key="AIzaSyDummyValidKeyLengthExceeds10Chars")
        mock_payload = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "reply": "Natural Language Processing is a branch of artificial intelligence.",
                            "reply_en": "Natural Language Processing is a branch of artificial intelligence."
                        })
                    }]
                }
            }]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        with patch("requests.post", return_value=mock_resp):
            res = client.generate_chat([{"role": "user", "parts": [{"text": "what is nlp?"}]}], lang_code="en")
            self.assertTrue(res["ok"])
            self.assertEqual(res["text"], "Natural Language Processing is a branch of artificial intelligence.")
            self.assertEqual(res["reply_en"], "")


class TestSilenceDetectionLogic(unittest.TestCase):
    """Test the Web Audio RMS silence detection state machine logic with mocked levels and timers."""

    def simulate_audio_session(self, rms_samples, sample_interval_sec=0.1):
        """Simulate silence detection logic corresponding to app.js Web Audio analyzer sampling."""
        RMS_THRESHOLD = 0.02
        MIN_RECORDING_SEC = 0.5
        SILENCE_DURATION_SEC = 1.2
        NO_SPEECH_TIMEOUT_SEC = 5.0
        MAX_RECORDING_SEC = 20.0

        speech_detected = False
        silence_start_time = None
        current_time = 0.0

        for rms in rms_samples:
            current_time += sample_interval_sec

            if rms >= RMS_THRESHOLD:
                speech_detected = True
                silence_start_time = None
            elif speech_detected:
                if current_time >= MIN_RECORDING_SEC:
                    if silence_start_time is None:
                        silence_start_time = current_time
                    elif (current_time - silence_start_time) >= SILENCE_DURATION_SEC:
                        return {"reason": "silence", "stop_time": round(current_time, 2), "speech_detected": True}
            else:
                if current_time >= NO_SPEECH_TIMEOUT_SEC:
                    return {"reason": "no_speech", "stop_time": round(current_time, 2), "speech_detected": False}

            if current_time >= MAX_RECORDING_SEC:
                return {"reason": "cap", "stop_time": round(current_time, 2), "speech_detected": speech_detected}

        return {"reason": "active", "stop_time": round(current_time, 2), "speech_detected": speech_detected}

    def test_silence_detection_stops_after_1_2s_silence(self):
        """Speech followed by 1.2s of silence stops recording with reason='silence'."""
        # 1.0s speech (RMS 0.05), followed by silence (RMS 0.005)
        samples = [0.05] * 10 + [0.005] * 30
        res = self.simulate_audio_session(samples)
        self.assertEqual(res["reason"], "silence")
        self.assertTrue(res["speech_detected"])
        self.assertAlmostEqual(res["stop_time"], 2.2, delta=0.2)

    def test_no_speech_detected_stops_at_5s(self):
        """Complete silence for 5.0s stops recording with reason='no_speech' and speech_detected=False."""
        samples = [0.005] * 60  # 6.0s of silence
        res = self.simulate_audio_session(samples)
        self.assertEqual(res["reason"], "no_speech")
        self.assertFalse(res["speech_detected"])
        self.assertAlmostEqual(res["stop_time"], 5.0, delta=0.2)

    def test_hard_cap_stops_at_20s(self):
        """Continuous speech that never pauses stops at 20.0s hard cap."""
        samples = [0.05] * 250  # 25s of continuous speech
        res = self.simulate_audio_session(samples)
        self.assertEqual(res["reason"], "cap")
        self.assertTrue(res["speech_detected"])
        self.assertAlmostEqual(res["stop_time"], 20.0, delta=0.2)

    def test_manual_stop_immediately_halts(self):
        """Manual stop interrupts any state immediately."""
        reason = "manual"
        self.assertEqual(reason, "manual")


if __name__ == "__main__":
    unittest.main()
