"""Flask web app for VaaniAI."""
import os
from flask import Flask, jsonify, request, send_from_directory

from nlp.languages import LANGUAGES
from nlp.pipeline import get_bot, process
from nlp.speech import transcribe_audio

app = Flask(__name__, static_folder="static", static_url_path="/static")
get_bot()  # train the intent model once at start-up


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/languages")
def languages():
    return jsonify([{"code": c, **v} for c, v in LANGUAGES.items()])


@app.post("/api/analyze")
def analyze_endpoint():
    data = request.get_json(silent=True) or {}
    result = process(data.get("text", ""), data.get("reply_to", "auto"),
                     data.get("translate_to", "en"), data.get("tz"))
    return (jsonify(result), 400) if "error" in result else jsonify(result)


@app.post("/api/transcribe")
def transcribe():
    f = request.files.get("audio")
    if not f:
        return jsonify({"ok": False, "error": "No audio file"}), 400
    res = transcribe_audio(f.read(), request.form.get("lang", "en"))
    return jsonify(res), (200 if res["ok"] else 422)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
