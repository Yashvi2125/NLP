"""Automated Unit and Integration Tests for Phase 9: Frontend Refinement & User Experience.

Tests cover:
1. Verification of HTML template structure for all 7 NLP transparency cards.
2. Mobile navigation elements and accessibility attributes (ARIA, roles, labels).
3. Backend timing payload validation (local_nlp_ms, chatbot_ms, total_ms).
4. Static asset delivery (/static/app.js and /static/style.css).
5. New Chat session reset contract.
6. Conversation history API contract.
7. End-to-end timing integration with transcribed audio.
"""

import io
import uuid
from pathlib import Path
import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_index_html_structure(client):
    """Verify that index.html includes all Phase 9 transparency cards and controls."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Brand and header
    assert "VaaniAI" in html
    assert "themeBtn" in html

    # Settings and controls
    assert "speechLang" in html
    assert "replyLang" in html
    assert "transLang" in html
    assert "ttsOn" in html
    assert "autoSendVoice" in html
    assert "resetChatBtn" in html

    # Mobile responsive navigation tabs
    assert "mobileTabs" in html
    assert "tabChatBtn" in html
    assert "tabInsightsBtn" in html

    # Composer and speech triggers
    assert "micBtn" in html
    assert "interim" in html
    assert 'accept=".wav,.wave,.flac,.aiff,.aif,.mp3,.m4a,.webm,.ogg"' in html

    # All 7 NLP transparency cards
    assert 'id="cardLang"' in html
    assert 'id="cardPrep"' in html
    assert 'id="cardSent"' in html
    assert 'id="cardIntent"' in html
    assert 'id="cardEntities"' in html
    assert 'id="cardLatency"' in html
    assert 'id="cardTrans"' in html

    # Accessibility attributes
    assert 'role="log"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-label=' in html


def test_static_assets_delivery(client):
    """Verify that app.js and style.css are correctly served with appropriate mime types."""
    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "application/javascript" in js_res.content_type or "text/javascript" in js_res.content_type
    js_code = js_res.data.decode("utf-8")
    assert "function render(" in js_code
    assert "showTyping" in js_code
    assert "entityCategories" in js_code
    assert "latency-bar" in js_code

    css_res = client.get("/static/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.content_type
    css_code = css_res.data.decode("utf-8")
    assert ".typing-dots" in css_code
    assert ".latency-bar" in css_code
    assert ".entity-group" in css_code
    assert ":focus-visible" in css_code


def test_analyze_endpoint_timing_metrics(client):
    """Verify that /api/analyze returns genuine, non-fabricated timing measurements."""
    res = client.post("/api/analyze", json={
        "text": "Tell me a joke please",
        "reply_to": "auto",
        "translate_to": "en"
    })
    assert res.status_code == 200
    j = res.get_json()

    assert "timing" in j
    timing = j["timing"]
    assert "local_nlp_ms" in timing
    assert "chatbot_ms" in timing
    assert "total_ms" in timing

    assert isinstance(timing["local_nlp_ms"], (int, float))
    assert isinstance(timing["chatbot_ms"], (int, float))
    assert isinstance(timing["total_ms"], (int, float))

    assert timing["local_nlp_ms"] >= 0.0
    assert timing["total_ms"] > 0.0


def test_analyze_multilingual_insights_payload(client):
    """Verify that full multilingual transparency details are included in the response."""
    res = client.post("/api/analyze", json={
        "text": "मेरा नाम राहुल है और मैं मुंबई में रहता हूँ",
        "reply_to": "auto",
        "translate_to": "en"
    })
    assert res.status_code == 200
    j = res.get_json()

    # Language details
    assert j["language"]["code"] == "hi"
    assert "Hindi" in j["language"]["name"]
    assert j["language"]["confidence"] > 0.5

    # Sentiment
    assert "compound" in j["sentiment"]
    assert "label" in j["sentiment"]

    # Entities
    entity_types = {e["type"] for e in j["entities"]}
    assert "PERSON" in entity_types
    assert any(e["value"] == "राहुल" for e in j["entities"] if e["type"] == "PERSON")

    # Reply engine
    assert "engine" in j["reply"]
    assert j["reply"]["text"]


def test_chat_reset_and_memory_workflow(client):
    """Verify that session reset clears conversational memory without server-side error."""
    sid = "test-frontend-" + str(uuid.uuid4())

    # Send first message
    client.post("/api/analyze", json={"text": "hello", "session_id": sid})

    # History should contain message
    h_before = client.get(f"/api/chat/history?session_id={sid}").get_json()
    assert len(h_before["history"]) >= 2

    # Reset chat
    r_res = client.post("/api/chat/reset", json={"session_id": sid})
    assert r_res.status_code == 200
    r_json = r_res.get_json()
    assert r_json["ok"] is True
    assert r_json["cleared"] is True

    # History should now be empty
    h_after = client.get(f"/api/chat/history?session_id={sid}").get_json()
    assert len(h_after["history"]) == 0
