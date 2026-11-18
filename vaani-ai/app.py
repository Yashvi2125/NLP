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


# Centralized mapping from UI "I speak" codes to Sarvam BCP-47 language codes
# Note: Hinglish is omitted as it is not a standalone dropdown option; mode is handled separately.
SARVAM_LANGUAGE_MAP = {
    "auto": "unknown",
    "en": "en-IN",
    "en-in": "en-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "gu": "gu-IN",
    "gu-in": "gu-IN",
    "mr": "mr-IN",
    "mr-in": "mr-IN",
    "bn": "bn-IN",
    "bn-in": "bn-IN",
    "ta": "ta-IN",
    "ta-in": "ta-IN",
    "te": "te-IN",
    "te-in": "te-IN",
    "ur": "ur-IN",
    "ur-in": "ur-IN",
    "ur-pk": "ur-IN",
    "kn": "kn-IN",
    "kn-in": "kn-IN",
    "ml": "ml-IN",
    "ml-in": "ml-IN",
    "pa": "pa-IN",
    "pa-in": "pa-IN",
    "od": "od-IN",
    "od-in": "od-IN",
    "or": "od-IN",
    "or-in": "od-IN",
}

MAX_STT_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@app.post("/api/stt")
def sarvam_stt():
    """Cloud Speech-to-Text endpoint powered by Sarvam AI (Saaras v4)."""
    api_key = (os.environ.get("SARVAM_API_KEY") or "").strip()
    if not api_key or api_key in ("your_key_here", "dummy_key", "placeholder"):
        return jsonify({
            "error": "Speech service not configured",
            "code": "SERVICE_UNAVAILABLE"
        }), 503

    f = request.files.get("audio")
    if not f:
        return jsonify({
            "error": "No audio file provided in request (use multipart/form-data field 'audio').",
            "code": "NO_FILE"
        }), 400

    filename = f.filename or "recording.webm"
    file_bytes = f.read()

    # Reject empty files
    if not file_bytes or len(file_bytes) == 0:
        return jsonify({
            "error": "Audio file is empty (0 bytes received).",
            "code": "EMPTY_AUDIO"
        }), 400

    # Reject oversized files (> 5 MB)
    if len(file_bytes) > MAX_STT_FILE_SIZE:
        size_mb = len(file_bytes) / (1024 * 1024)
        return jsonify({
            "error": f"Audio file ({size_mb:.1f} MB) exceeds maximum allowed limit of 5 MB.",
            "code": "FILE_TOO_LARGE"
        }), 400

    # Reject silent or micro-payload audio
    if len(file_bytes) < 200:
        return jsonify({
            "error": "Audio stream contains no detectable speech data.",
            "code": "SILENT_AUDIO"
        }), 400

    # Map language
    user_lang = (request.form.get("lang") or "auto").strip().lower()
    target_code = SARVAM_LANGUAGE_MAP.get(user_lang)
    if not target_code:
        return jsonify({
            "error": f"Language '{user_lang}' is not supported by Sarvam AI speech service. Please use browser speech recognition.",
            "code": "UNSUPPORTED_LANGUAGE"
        }), 400

    start_time = time.perf_counter()
    import logging
    import unicodedata

    # Determine mode: default transcribe
    mode = "transcribe"

    try:
        from sarvamai import SarvamAI
        client = SarvamAI(api_subscription_key=api_key)

        # Transcribe directly using (filename, bytes) tuple
        response = client.speech_to_text.transcribe(
            file=(filename, file_bytes),
            model="saaras:v4",
            mode=mode,
            language_code=target_code,
        )

        transcript = (response.transcript or "").strip()
        detected_lang = response.language_code or target_code
        latency = round(time.perf_counter() - start_time, 3)

        if not transcript:
            logging.info("STT completed: status=422, latency=%.3fs, lang=%s (silent/empty transcript)", latency, detected_lang)
            return jsonify({
                "error": "No speech detected in audio. Please speak clearly into the microphone.",
                "code": "SILENT_AUDIO"
            }), 422

        # Normalize Unicode NFC and trim
        normalized_text = unicodedata.normalize("NFC", transcript)

        # Log ONLY status, latency, and language. NEVER log audio or transcript.
        logging.info("STT completed: status=200, latency=%.3fs, lang=%s", latency, detected_lang)

        return jsonify({
            "text": normalized_text,
            "language": detected_lang,
            "provider": "sarvam"
        }), 200

    except Exception as exc:
        latency = round(time.perf_counter() - start_time, 3)
        # Check if error is related to format and ffmpeg is available
        from nlp.speech import has_ffmpeg, convert_to_wav
        if has_ffmpeg():
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".webm", delete=False) as in_f:
                    in_f.write(file_bytes)
                    in_path = in_f.name
                out_path = in_path + ".wav"
                if convert_to_wav(in_path, out_path) and os.path.exists(out_path):
                    with open(out_path, "rb") as wf:
                        converted_bytes = wf.read()
                    os.unlink(in_path)
                    os.unlink(out_path)
                    res = client.speech_to_text.transcribe(
                        file=("audio.wav", converted_bytes),
                        model="saaras:v4",
                        mode=mode,
                        language_code=target_code,
                    )
                    transcript = (res.transcript or "").strip()
                    detected_lang = res.language_code or target_code
                    if transcript:
                        normalized_text = unicodedata.normalize("NFC", transcript)
                        logging.info("STT completed with ffmpeg conversion: status=200, latency=%.3fs, lang=%s", latency, detected_lang)
                        return jsonify({
                            "text": normalized_text,
                            "language": detected_lang,
                            "provider": "sarvam"
                        }), 200
            except Exception:
                pass

        logging.error("STT failed: status=500, latency=%.3fs, error=%s", latency, type(exc).__name__)
        return jsonify({
            "error": "Failed to transcribe audio via speech service.",
            "code": "STT_ERROR"
        }), 500


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
