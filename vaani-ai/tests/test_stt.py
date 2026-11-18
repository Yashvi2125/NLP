"""Tests for Sarvam AI Speech-to-Text (/api/stt) endpoint."""

import io
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure app can be imported
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import app, SARVAM_LANGUAGE_MAP


class TestSarvamSTTEndpoint(unittest.TestCase):
    """Unit and mock tests for POST /api/stt."""

    def setUp(self):
        self.app = app
        self.client = app.test_client()

    def test_missing_api_key_returns_503(self):
        """Route returns 503 when SARVAM_API_KEY is missing or placeholder."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": ""}, clear=False):
            data = {"audio": (io.BytesIO(b"RIFFdummywavdata1234567890" * 20), "test.wav")}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 503)
            json_data = resp.get_json()
            self.assertEqual(json_data.get("code"), "SERVICE_UNAVAILABLE")
            self.assertIn("Speech service not configured", json_data.get("error", ""))

    def test_placeholder_api_key_returns_503(self):
        """Route returns 503 when SARVAM_API_KEY is 'your_key_here'."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": "your_key_here"}, clear=False):
            data = {"audio": (io.BytesIO(b"RIFFdummywavdata1234567890" * 20), "test.wav")}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 503)

    def test_empty_audio_upload_rejected(self):
        """Empty audio upload (0 bytes) is rejected with 400."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test_mock_key_12345"}):
            data = {"audio": (io.BytesIO(b""), "empty.wav")}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 400)
            json_data = resp.get_json()
            self.assertEqual(json_data.get("code"), "EMPTY_AUDIO")

    def test_oversized_audio_upload_rejected(self):
        """Audio upload exceeding 5 MB is rejected with 400."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test_mock_key_12345"}):
            oversized_data = b"0" * (5 * 1024 * 1024 + 1024)  # 5 MB + 1 KB
            data = {"audio": (io.BytesIO(oversized_data), "big.wav")}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 400)
            json_data = resp.get_json()
            self.assertEqual(json_data.get("code"), "FILE_TOO_LARGE")

    def test_silent_or_too_short_audio_rejected(self):
        """Audio under 200 bytes is rejected with 400 SILENT_AUDIO."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test_mock_key_12345"}):
            data = {"audio": (io.BytesIO(b"short"), "short.wav")}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 400)
            json_data = resp.get_json()
            self.assertEqual(json_data.get("code"), "SILENT_AUDIO")

    def test_missing_audio_field_rejected(self):
        """Request without 'audio' multipart field returns 400 NO_FILE."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test_mock_key_12345"}):
            resp = self.client.post("/api/stt", data={"lang": "hi-IN"}, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 400)
            json_data = resp.get_json()
            self.assertEqual(json_data.get("code"), "NO_FILE")

    def test_unsupported_foreign_language_rejected(self):
        """Unsupported foreign language (e.g., Spanish) returns 400 directing to browser fallback."""
        with patch.dict(os.environ, {"SARVAM_API_KEY": "test_mock_key_12345"}):
            data = {
                "audio": (io.BytesIO(b"RIFF" + b"X" * 300), "sample.wav"),
                "lang": "es-ES"
            }
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 400)
            json_data = resp.get_json()
            self.assertEqual(json_data.get("code"), "UNSUPPORTED_LANGUAGE")

    def test_api_key_never_leaked_in_responses(self):
        """API key must never appear in response body, headers, or error messages."""
        secret_key = "sk_secret_mock_test_token_never_leak_987654321"
        with patch.dict(os.environ, {"SARVAM_API_KEY": secret_key}):
            # Test error responses
            resp = self.client.post("/api/stt", data={}, content_type="multipart/form-data")
            self.assertNotIn(secret_key, resp.get_data(as_text=True))
            for h_val in resp.headers.values():
                self.assertNotIn(secret_key, str(h_val))

            # Test oversized error
            oversized = io.BytesIO(b"X" * (6 * 1024 * 1024))
            resp = self.client.post("/api/stt", data={"audio": (oversized, "test.wav")}, content_type="multipart/form-data")
            self.assertNotIn(secret_key, resp.get_data(as_text=True))

    @patch("sarvamai.SarvamAI")
    def test_mocked_sarvam_success_json_shape(self, mock_sarvam_cls):
        """Mocked Sarvam call verifies JSON shape: {text, language, provider} and Unicode NFC."""
        mock_client = MagicMock()
        mock_sarvam_cls.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.transcript = "  नमस्ते, आप कैसे हैं?  "
        mock_resp.language_code = "hi-IN"
        mock_client.speech_to_text.transcribe.return_value = mock_resp

        with patch.dict(os.environ, {"SARVAM_API_KEY": "valid_test_mock_key"}):
            dummy_audio = io.BytesIO(b"RIFF" + b"\x00" * 400)
            data = {"audio": (dummy_audio, "voice.webm"), "lang": "hi-IN"}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")

            self.assertEqual(resp.status_code, 200)
            res = resp.get_json()

            # Verify exact required JSON keys
            self.assertIn("text", res)
            self.assertIn("language", res)
            self.assertIn("provider", res)
            self.assertEqual(res["provider"], "sarvam")
            self.assertEqual(res["language"], "hi-IN")
            self.assertEqual(res["text"], "नमस्ते, आप कैसे हैं?")  # Trimmed & NFC normalized
            self.assertNotIn("key", res)
            self.assertNotIn("api_key", res)

    @patch("sarvamai.SarvamAI")
    def test_mocked_sarvam_empty_speech_returns_422(self, mock_sarvam_cls):
        """Mocked empty transcription from Sarvam returns 422 SILENT_AUDIO."""
        mock_client = MagicMock()
        mock_sarvam_cls.return_value = mock_client

        mock_resp = MagicMock()
        mock_resp.transcript = "   "
        mock_resp.language_code = "hi-IN"
        mock_client.speech_to_text.transcribe.return_value = mock_resp

        with patch.dict(os.environ, {"SARVAM_API_KEY": "valid_test_mock_key"}):
            dummy_audio = io.BytesIO(b"RIFF" + b"\x00" * 400)
            data = {"audio": (dummy_audio, "voice.webm"), "lang": "hi-IN"}
            resp = self.client.post("/api/stt", data=data, content_type="multipart/form-data")
            self.assertEqual(resp.status_code, 422)
            res = resp.get_json()
            self.assertEqual(res.get("code"), "SILENT_AUDIO")


class TestSarvamSTTLive(unittest.TestCase):
    """Live integration tests against Sarvam AI API."""

    def test_live_sarvam_stt(self):
        """Run live test if real SARVAM_API_KEY and audio fixture are present, otherwise skip clearly."""
        api_key = (os.environ.get("SARVAM_API_KEY") or "").strip()
        if not api_key or api_key in ("your_key_here", "dummy_key", "placeholder", ""):
            self.skipTest("Skipping live Sarvam STT test: SARVAM_API_KEY is not set or is a placeholder.")

        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "audio"
        clip_path = fixture_dir / "sample_test.wav"
        if not clip_path.exists():
            self.skipTest(f"Skipping live Sarvam STT test: audio fixture not found at {clip_path}")

        client = app.test_client()
        with open(clip_path, "rb") as af:
            data = {
                "audio": (af, "sample_test.wav"),
                "lang": "en-IN"
            }
            resp = client.post("/api/stt", data=data, content_type="multipart/form-data")

        self.assertEqual(resp.status_code, 200)
        res = resp.get_json()
        self.assertIn("text", res)
        self.assertIn("language", res)
        self.assertEqual(res["provider"], "sarvam")
        self.assertTrue(len(res["text"]) > 0)
        print(f"\n[LIVE TEST SUCCESS] Transcribed: '{res['text']}', Language: {res['language']}")


if __name__ == "__main__":
    unittest.main()
