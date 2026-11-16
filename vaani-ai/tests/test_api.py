import pytest
from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200 and b"VaaniAI" in r.data


def test_languages(client):
    langs = client.get("/api/languages").get_json()
    assert {"en", "hi", "es"} <= {l["code"] for l in langs}


def test_analyze_ok(client):
    r = client.post("/api/analyze", json={"text": "What time is it?", "tz": "Asia/Kolkata"})
    j = r.get_json()
    assert r.status_code == 200 and j["intent"]["name"] == "ask_time"
    assert "current time" in j["reply"]["text"].lower()
    assert {"language", "preprocessing", "sentiment", "intent", "entities", "translation", "reply"} <= set(j)


def test_analyze_empty_is_400(client):
    assert client.post("/api/analyze", json={"text": ""}).status_code == 400


def test_analyze_bad_json_is_400(client):
    assert client.post("/api/analyze", data="nope").status_code == 400


def test_translate_request_reply(client):
    j = client.post("/api/analyze", json={"text": "translate good morning to Hindi"}).get_json()
    assert j["intent"]["name"] == "translate_request" and "सुप्रभात" in j["reply"]["text"]


def test_transcribe_requires_file(client):
    assert client.post("/api/transcribe").status_code == 400
