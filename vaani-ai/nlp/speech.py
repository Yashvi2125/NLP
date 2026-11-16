"""Optional server-side speech-to-text for uploaded WAV/FLAC files (needs internet + SpeechRecognition).

Live microphone input is handled in the browser with the Web Speech API (see static/app.js).
"""
import io

from .languages import LANGUAGES


def transcribe_audio(file_bytes: bytes, lang: str = "en") -> dict:
    try:
        import speech_recognition as sr
    except ImportError:
        return {"ok": False, "error": "SpeechRecognition is not installed (pip install SpeechRecognition)."}
    r = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(file_bytes)) as src:
            audio = r.record(src)
        code = LANGUAGES.get(lang, LANGUAGES["en"])["speech"]
        text = r.recognize_google(audio, language=code)
        return {"ok": True, "text": text, "engine": "Google Web Speech API"}
    except Exception as e:  # unreadable file, no internet, unintelligible audio...
        return {"ok": False, "error": f"Could not transcribe audio: {e}"}
