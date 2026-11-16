"""Automated Unit and Integration Tests for Phase 8: Speech-to-Text (STT) Module.

Tests cover:
1. Multilingual BCP-47 speech recognition code resolution for all 20 languages + Hinglish.
2. Audio payload validation (empty, oversized, unsupported extensions, valid extensions).
3. Flask endpoint /api/transcribe validation (missing file, 0-byte, invalid format, corrupted audio).
4. Silent audio handling and graceful error code discrimination.
5. Guaranteed temporary file cleanup on disk (no orphan files).
6. Real-audio transcription and Word Error Rate (WER) measurement.
7. End-to-end integration: speech transcription -> pipeline analysis -> hybrid chatbot response.
8. Multi-turn conversational memory persistence following audio transcription.
9. auto_analyze parameter in /api/transcribe.
"""

import io
import os
import struct
import tempfile
import uuid
import wave
from pathlib import Path

import pytest
from app import app
from nlp.languages import LANGUAGES, HINGLISH
from nlp.speech import (
    MAX_AUDIO_SIZE_BYTES,
    NATIVE_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    get_speech_language,
    transcribe_audio,
    validate_audio_file,
)
from scripts.evaluate_speech import compute_cer, compute_wer


@pytest.fixture
def client():
    return app.test_client()


def create_silent_wav(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate in-memory PCM WAV bytes containing pure silence."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        num_frames = int(duration_sec * sample_rate)
        w.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


# -------------------------------------------------------------
# 1. Multilingual Speech Code Resolution
# -------------------------------------------------------------

def test_speech_language_resolution_all_20_languages():
    """Verify BCP-47 speech recognition code mapping for all 20 languages."""
    expected = {
        "en": "en-IN",
        "hi": "hi-IN",
        "mr": "mr-IN",
        "gu": "gu-IN",
        "bn": "bn-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "ur": "ur-PK",
        "es": "es-ES",
        "fr": "fr-FR",
        "de": "de-DE",
        "it": "it-IT",
        "pt": "pt-BR",
        "nl": "nl-NL",
        "ru": "ru-RU",
        "ar": "ar-SA",
        "ja": "ja-JP",
        "zh": "zh-CN",
        "ko": "ko-KR",
    }
    for code, expected_speech in expected.items():
        assert get_speech_language(code) == expected_speech, f"Mismatch for language {code}"

    # Hinglish mapping to Indian English bilingual model
    assert get_speech_language("hinglish") == "en-IN"

    # Default fallback on empty/none
    assert get_speech_language(None) == "en-IN"
    assert get_speech_language("") == "en-IN"


# -------------------------------------------------------------
# 2. Audio Validation Unit Tests
# -------------------------------------------------------------

def test_audio_validation_empty_bytes():
    valid, err, ext = validate_audio_file(b"")
    assert not valid
    assert "empty" in err.lower()


def test_audio_validation_oversized():
    huge_bytes = b"0" * (MAX_AUDIO_SIZE_BYTES + 1024)
    valid, err, ext = validate_audio_file(huge_bytes, "test.wav")
    assert not valid
    assert "exceeds" in err.lower()


def test_audio_validation_unsupported_extension():
    valid, err, ext = validate_audio_file(b"sampledata", "payload.exe")
    assert not valid
    assert "unsupported" in err.lower()
    assert ext == ".exe"


def test_audio_validation_supported_extensions():
    for ext in [".wav", ".aiff", ".flac", ".mp3", ".m4a", ".webm", ".ogg"]:
        valid, err, resolved_ext = validate_audio_file(b"sampledata", f"sample{ext}")
        assert valid is True
        assert err is None
        assert resolved_ext == ext


# -------------------------------------------------------------
# 3. Flask /api/transcribe Endpoint Validation
# -------------------------------------------------------------

def test_api_transcribe_missing_file_400(client):
    res = client.post("/api/transcribe")
    assert res.status_code == 400
    j = res.get_json()
    assert j["ok"] is False
    assert j["code"] == "NO_FILE"


def test_api_transcribe_empty_file_400(client):
    data = {"audio": (io.BytesIO(b""), "empty.wav")}
    res = client.post("/api/transcribe", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    j = res.get_json()
    assert j["ok"] is False
    assert j["code"] == "VALIDATION_ERROR"


def test_api_transcribe_unsupported_format_400(client):
    data = {"audio": (io.BytesIO(b"fake binary"), "malware.exe")}
    res = client.post("/api/transcribe", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    j = res.get_json()
    assert j["ok"] is False
    assert j["code"] == "VALIDATION_ERROR"


def test_api_transcribe_corrupted_wav_422(client):
    corrupted_data = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00corrupt-bytes"
    data = {"audio": (io.BytesIO(corrupted_data), "corrupted.wav")}
    res = client.post("/api/transcribe", data=data, content_type="multipart/form-data")
    assert res.status_code == 422
    j = res.get_json()
    assert j["ok"] is False
    assert j["code"] == "CORRUPTED_AUDIO"


# -------------------------------------------------------------
# 4. Silent Audio Handling
# -------------------------------------------------------------

def test_silent_wav_audio_handling():
    silent_bytes = create_silent_wav(duration_sec=1.5)
    res = transcribe_audio(silent_bytes, lang="en", filename="silence.wav")
    assert res["ok"] is False
    assert res["code"] == "NO_SPEECH_DETECTED"
    assert "no speech" in res["error"].lower()


# -------------------------------------------------------------
# 5. Guaranteed Temporary File Cleanup
# -------------------------------------------------------------

def test_temporary_file_cleanup():
    temp_dir = tempfile.gettempdir()
    before_files = set(os.listdir(temp_dir))

    # Transcribe silent audio
    silent_bytes = create_silent_wav(duration_sec=1.0)
    transcribe_audio(silent_bytes, lang="en", filename="cleanup_test.wav")

    after_files = set(os.listdir(temp_dir))
    new_files = after_files - before_files

    # Verify no dangling .wav temporary files created by our function were left behind
    dangling_wavs = [f for f in new_files if f.endswith(".wav") and "cleanup_test" in f]
    assert len(dangling_wavs) == 0


# -------------------------------------------------------------
# 6. Real-Audio Transcription & WER Verification
# -------------------------------------------------------------

def test_real_audio_transcription():
    sample_file = Path(__file__).parent / "test_audio" / "hello_time.wav"
    if not sample_file.exists():
        pytest.skip("Test sample audio file not found")

    with open(sample_file, "rb") as f:
        audio_bytes = f.read()

    res = transcribe_audio(audio_bytes, lang="en", filename=sample_file.name)
    assert res["ok"] is True
    assert "time" in res["text"].lower()

    wer = compute_wer("hello what time is it", res["text"])
    cer = compute_cer("hello what time is it", res["text"])
    assert wer <= 0.20, f"WER too high: {wer:.1%}"
    assert cer <= 0.20, f"CER too high: {cer:.1%}"
    assert res["duration_sec"] > 0.0
    assert res["latency_ms"] > 0.0


# -------------------------------------------------------------
# 7. End-to-End Chatbot & Memory Integration
# -------------------------------------------------------------

def test_transcription_chatbot_pipeline_integration(client):
    sample_file = Path(__file__).parent / "test_audio" / "tell_joke.wav"
    if not sample_file.exists():
        pytest.skip("Test sample audio file not found")

    # Step 1: Transcribe audio
    with open(sample_file, "rb") as f:
        audio_bytes = f.read()

    data = {"audio": (io.BytesIO(audio_bytes), "tell_joke.wav"), "lang": "en"}
    t_res = client.post("/api/transcribe", data=data, content_type="multipart/form-data")
    assert t_res.status_code == 200
    t_json = t_res.get_json()
    assert t_json["ok"] is True
    transcribed_text = t_json["text"]
    assert "joke" in transcribed_text.lower()

    # Step 2: Pass transcribed text into /api/analyze with session_id
    sid = "speech-sess-" + str(uuid.uuid4())
    a_res = client.post("/api/analyze", json={
        "text": transcribed_text,
        "session_id": sid,
        "reply_to": "auto",
        "translate_to": "en",
    })
    assert a_res.status_code == 200
    a_json = a_res.get_json()
    assert a_json["intent"]["name"] == "joke"
    assert a_json["reply"]["text"]
    assert a_json["session_id"] == sid

    # Step 3: Verify conversational memory holds the speech turn
    h_res = client.get(f"/api/chat/history?session_id={sid}")
    assert h_res.status_code == 200
    h_json = h_res.get_json()
    assert len(h_json["history"]) >= 2
    assert h_json["history"][0]["role"] == "user"
    assert h_json["history"][0]["text"] == transcribed_text


def test_api_transcribe_auto_analyze_flag(client):
    sample_file = Path(__file__).parent / "test_audio" / "hello_time.wav"
    if not sample_file.exists():
        pytest.skip("Test sample audio file not found")

    with open(sample_file, "rb") as f:
        audio_bytes = f.read()

    sid = "auto-speech-" + str(uuid.uuid4())
    data = {
        "audio": (io.BytesIO(audio_bytes), "hello_time.wav"),
        "lang": "en",
        "auto_analyze": "true",
        "session_id": sid,
    }
    res = client.post("/api/transcribe", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    j = res.get_json()
    assert j["ok"] is True
    assert "analysis" in j
    assert j["analysis"]["intent"]["name"] == "ask_time"
    assert j["analysis"]["session_id"] == sid
