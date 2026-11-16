"""Comprehensive End-to-End System Integration & Render Deployment Tests for Phase 10.

Tests cover:
1. Health check endpoint (/api/health) returns 200 with status, version, uptime, and memory metrics.
2. Defense-in-depth HTTP security headers (nosniff, SAMEORIGIN, strict-origin-when-cross-origin).
3. Payload limits (413 handler for oversized requests).
4. Full end-to-end user journey:
   Audio upload -> Speech transcription -> Pipeline analysis -> Multilingual reply ->
   Contextual multi-turn follow-up -> Memory session reset -> Verification of clean state.
5. Concurrent multi-user session isolation (no cross-talk).
6. Memory manager automatic TTL expiration.
7. Cross-platform path portability and deployment configuration files (Procfile, render.yaml, requirements.txt).
"""

import io
import json
import os
import time
import uuid
from pathlib import Path

import pytest
from app import app
from nlp.memory import MemoryManager, SessionMemory


@pytest.fixture
def client():
    return app.test_client()


# -------------------------------------------------------------
# 1. Health Check Endpoint Tests
# -------------------------------------------------------------

def test_api_health_endpoint(client):
    """Verify /api/health returns valid system operational metrics."""
    res = client.get("/api/health")
    assert res.status_code == 200
    j = res.get_json()

    assert j["status"] == "healthy"
    assert j["version"] == "2.0.0"
    assert "uptime_sec" in j
    assert j["uptime_sec"] >= 0.0
    assert "intent_model_fitted" in j
    assert j["intent_model_fitted"] is True
    assert j["languages_supported"] >= 20
    assert "active_sessions" in j


# -------------------------------------------------------------
# 2. Security Headers & Payload Guard Tests
# -------------------------------------------------------------

def test_security_headers_present(client):
    """Verify production security headers are attached to all HTTP responses."""
    res = client.get("/")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_413_payload_too_large_handler(client):
    """Verify that oversized payloads trigger the custom 413 JSON handler."""
    huge_data = b"X" * (17 * 1024 * 1024)  # 17 MB > 16 MB limit
    res = client.post(
        "/api/transcribe",
        data={"audio": (io.BytesIO(huge_data), "huge.wav")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 413
    j = res.get_json()
    assert j["ok"] is False
    assert j["code"] == "PAYLOAD_TOO_LARGE"


# -------------------------------------------------------------
# 3. End-to-End User Journey Workflow
# -------------------------------------------------------------

def test_full_end_to_end_journey(client):
    """Execute complete end-to-end conversational workflow across all modules."""
    sample_wav = Path(__file__).parent / "test_audio" / "hello_time.wav"
    if not sample_wav.exists():
        pytest.skip("Sample test audio not found")

    sid = "journey-" + str(uuid.uuid4())

    # Step 1: Upload audio file and transcribe
    with open(sample_wav, "rb") as f:
        audio_bytes = f.read()

    trans_res = client.post(
        "/api/transcribe",
        data={"audio": (io.BytesIO(audio_bytes), "hello_time.wav"), "lang": "en"},
        content_type="multipart/form-data"
    )
    assert trans_res.status_code == 200
    t_data = trans_res.get_json()
    assert t_data["ok"] is True
    transcript = t_data["text"]

    # Step 2: Send transcribed text into the NLP analysis pipeline
    ana_res = client.post("/api/analyze", json={
        "text": transcript,
        "session_id": sid,
        "reply_to": "auto",
        "translate_to": "hi"
    })
    assert ana_res.status_code == 200
    a_data = ana_res.get_json()

    assert a_data["intent"]["name"] == "ask_time"
    assert a_data["session_id"] == sid
    assert a_data["timing"]["local_nlp_ms"] >= 0.0
    assert a_data["reply"]["text"]
    assert a_data["translation"]["target"] == "hi"

    # Step 3: Multi-turn follow-up with Hindi text
    followup_res = client.post("/api/analyze", json={
        "text": "धन्यवाद, आज की तारीख क्या है?",
        "session_id": sid,
        "reply_to": "auto",
        "translate_to": "en"
    })
    assert followup_res.status_code == 200
    f_data = followup_res.get_json()
    assert f_data["intent"]["name"] in ("ask_date", "ask_time", "thanks", "greeting")

    # Step 4: Verify conversation history
    hist_res = client.get(f"/api/chat/history?session_id={sid}")
    assert hist_res.status_code == 200
    h_data = hist_res.get_json()
    assert len(h_data["history"]) >= 4

    # Step 5: Reset conversation
    reset_res = client.post("/api/chat/reset", json={"session_id": sid})
    assert reset_res.status_code == 200
    assert reset_res.get_json()["cleared"] is True

    # Step 6: Verify clean history
    empty_hist = client.get(f"/api/chat/history?session_id={sid}").get_json()
    assert len(empty_hist["history"]) == 0


# -------------------------------------------------------------
# 4. Concurrent Sessions Isolation Test
# -------------------------------------------------------------

def test_concurrent_sessions_isolation(client):
    """Verify that multiple concurrent user sessions maintain strict context isolation."""
    sessions = [f"conc-sess-{i}-{uuid.uuid4()}" for i in range(5)]
    queries = [
        "What time is it?",
        "Tell me a joke",
        "मेरा नाम राहुल है",
        "Bonjour comment allez vous",
        "Who is the CEO of Google?",
    ]

    # Post queries across sessions
    for sid, q in zip(sessions, queries):
        res = client.post("/api/analyze", json={"text": q, "session_id": sid})
        assert res.status_code == 200

    # Verify each session contains only its own history
    for sid, q in zip(sessions, queries):
        h = client.get(f"/api/chat/history?session_id={sid}").get_json()
        assert len(h["history"]) >= 2
        assert h["history"][0]["text"] == q


# -------------------------------------------------------------
# 5. Session Memory TTL Expiration Test
# -------------------------------------------------------------

def test_session_ttl_expiration():
    """Verify that inactive sessions are purged when TTL expires."""
    mgr = MemoryManager(ttl_seconds=0.05, max_turns=5)
    s = mgr.get_or_create("expiring-session")
    s.add_turn("user", "test")
    assert "expiring-session" in mgr.sessions

    # Sleep past TTL
    time.sleep(0.08)
    purged = mgr.clean_expired_sessions()
    assert purged >= 1
    assert "expiring-session" not in mgr.sessions


# -------------------------------------------------------------
# 6. Render Deployment Configuration & Portability
# -------------------------------------------------------------

def test_render_deployment_files_exist():
    """Verify presence and validity of required Render deployment files."""
    root = Path(__file__).resolve().parent.parent

    # 1. Procfile
    procfile = root / "Procfile"
    assert procfile.exists(), "Procfile missing"
    assert "gunicorn app:app" in procfile.read_text(encoding="utf-8")

    # 2. render.yaml
    render_yaml = root / "render.yaml"
    assert render_yaml.exists(), "render.yaml missing"
    content = render_yaml.read_text(encoding="utf-8")
    assert "type: web" in content
    assert "healthCheckPath: /api/health" in content

    # 3. requirements.txt
    reqs = root / "requirements.txt"
    assert reqs.exists(), "requirements.txt missing"
    req_text = reqs.read_text(encoding="utf-8")
    for pkg in ["flask", "gunicorn", "scikit-learn", "vaderSentiment", "requests", "SpeechRecognition"]:
        assert pkg.lower() in req_text.lower(), f"{pkg} missing from requirements.txt"
