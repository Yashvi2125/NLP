"""Flask web app for VaaniAI — Voice-to-Text & Multilingual Conversational Assistant."""

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Track application start time for uptime monitoring
START_TIME = time.time()

# Load environment variables early from local .env if present
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

from flask import Flask, jsonify, request, send_from_directory

from nlp.languages import LANGUAGES
from nlp.pipeline import get_bot, process
from nlp.speech import transcribe_audio

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Request payload limit: 16 MB maximum
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# Pre-warm local model and session memory once at start-up
get_bot()


# -------------------------------------------------------------
# Security & Headers Hook
# -------------------------------------------------------------

@app.after_request
def apply_security_headers(response):
    """Enforce defense-in-depth security headers on all responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "microphone=*"
    return response


@app.errorhandler(413)
def request_entity_too_large(error):
    """Graceful JSON handler when request exceeds MAX_CONTENT_LENGTH."""
    return jsonify({
        "ok": False,
        "error": "Request entity exceeds the maximum allowed payload size of 16 MB.",
        "code": "PAYLOAD_TOO_LARGE",
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    """Secure error handler to prevent internal stack trace leakage."""
    return jsonify({
        "ok": False,
        "error": "An internal server error occurred. Please try again later.",
        "code": "INTERNAL_SERVER_ERROR",
    }), 500


# -------------------------------------------------------------
# Frontend Routes
# -------------------------------------------------------------

@app.get("/")
def index():
    return send_from_directory("static", "index.html")


# -------------------------------------------------------------
# Health Check & Monitoring Endpoint
# -------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Health check endpoint for Render, load balancers, and monitoring."""
    bot = get_bot()
    uptime_sec = round(time.time() - START_TIME, 1)

    mem_mb = None
    try:
        import psutil
        process_info = psutil.Process()
        mem_mb = round(process_info.memory_info().rss / (1024 * 1024), 1)
    except Exception:
        pass

    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "uptime_sec": uptime_sec,
        "memory_mb": mem_mb,
        "gemini_configured": bot.gemini.is_configured,
        "gemini_model": bot.gemini.model if bot.gemini.is_configured else None,
        "intent_model_fitted": bot.clf.fitted,
        "languages_supported": len(LANGUAGES) + 1,  # 19 ISO standard codes + Hinglish
        "active_sessions": bot.memory.count_active_sessions(),
    }), 200


# -------------------------------------------------------------
# Core API Endpoints
# -------------------------------------------------------------

@app.get("/api/languages")
def languages():
    return jsonify([{"code": c, **v} for c, v in LANGUAGES.items()])


@app.post("/api/analyze")
def analyze_endpoint():
    data = request.get_json(silent=True) or {}
    result = process(
        text=data.get("text", ""),
        reply_to=data.get("reply_to", "auto"),
        translate_to=data.get("translate_to", "en"),
        tz=data.get("tz") or "Asia/Kolkata",
        session_id=data.get("session_id"),
        speech_lang=data.get("speech_lang"),
    )
    return (jsonify(result), 400) if "error" in result else jsonify(result)


@app.post("/api/chat/reset")
def reset_session_endpoint():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"ok": False, "error": "Missing session_id parameter", "code": "MISSING_SESSION_ID"}), 400
    cleared = get_bot().memory.reset_session(session_id)
    return jsonify({"ok": True, "session_id": session_id, "cleared": cleared})


@app.get("/api/chat/history")
def get_history_endpoint():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"ok": False, "error": "Missing session_id parameter", "code": "MISSING_SESSION_ID"}), 400
    session = get_bot().memory.get_or_create(session_id)
    return jsonify({
        "ok": True,
        "session_id": session_id,
        "history": session.get_history(),
        "context_entities": session.context_entities,
    })


@app.post("/api/transcribe")
def transcribe():
    f = request.files.get("audio")
    if not f:
        return jsonify({
            "ok": False,
            "error": "No audio file provided in request (use multipart/form-data field 'audio').",
            "code": "NO_FILE"
        }), 400

    filename = f.filename or "audio.wav"
    file_bytes = f.read()

    res = transcribe_audio(
        file_bytes=file_bytes,
        lang=request.form.get("lang", "en"),
        filename=filename,
    )

    if not res["ok"]:
        status_code = 400 if res.get("code") == "VALIDATION_ERROR" else 422
        return jsonify(res), status_code

    # Optional instant pipeline analysis if requested by client
    if request.form.get("auto_analyze") in ("true", "1") and res.get("text"):
        session_id = request.form.get("session_id")
        reply_to = request.form.get("reply_to", "auto")
        translate_to = request.form.get("translate_to", "en")
        tz = request.form.get("tz")
        analysis = process(
            text=res["text"],
            reply_to=reply_to,
            translate_to=translate_to,
            tz=tz,
            session_id=session_id,
        )
        res["analysis"] = analysis

    return jsonify(res), 200


# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    app.run(host="0.0.0.0", port=port, debug=debug)
