"""Server-side audio transcription module for Vaani AI.

Features:
- Robust audio format validation (WAV, AIFF, FLAC, MP3, M4A, WebM, OGG).
- File size bounds checking (max 10 MB).
- Multi-language BCP-47 speech recognition code resolution.
- Safe temporary-file handling with guaranteed cleanup.
- Graceful error discrimination (silence, corruption, network failure, missing codecs).
- FFmpeg bridge for compressed formats where system codecs are installed.
- Performance profiling (latency and audio duration).
"""

import io
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from .languages import LANGUAGES, HINGLISH

# Maximum allowed audio upload size (10 MB)
MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024

# Maximum allowed duration in seconds (2 minutes for responsive conversational turns)
MAX_AUDIO_DURATION_SEC = 120.0

# Supported audio file extensions
SUPPORTED_EXTENSIONS = {
    ".wav", ".wave", ".aiff", ".aif", ".flac",
    ".mp3", ".m4a", ".webm", ".ogg"
}

# Native formats decodable directly by SpeechRecognition / Python standard library
NATIVE_EXTENSIONS = {".wav", ".wave", ".aiff", ".aif", ".flac"}


def has_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system PATH."""
    return shutil.which("ffmpeg") is not None


def get_speech_language(lang_code: Optional[str] = None) -> str:
    """Resolve an internal language code or BCP-47 tag to an engine-compatible speech recognition code.

    Examples:
        'hi' -> 'hi-IN'
        'gu' -> 'gu-IN'
        'hinglish' -> 'en-IN' (Indian English bilingual acoustic model)
        'es' -> 'es-ES'
        'en' -> 'en-IN'
    """
    if not lang_code:
        return "en-IN"

    clean = lang_code.strip().lower()

    # Check for direct internal language registry
    if clean == HINGLISH:
        return "en-IN"

    if clean in LANGUAGES:
        return LANGUAGES[clean].get("speech", "en-IN")

    # If already a BCP-47 tag (e.g., 'hi-IN', 'en-US', 'fr-FR'), validate or return
    for lang_info in LANGUAGES.values():
        if lang_info.get("speech", "").lower() == clean:
            return lang_info["speech"]

    # Common short aliases
    aliases = {
        "english": "en-IN",
        "hindi": "hi-IN",
        "gujarati": "gu-IN",
        "marathi": "mr-IN",
        "bengali": "bn-IN",
        "tamil": "ta-IN",
        "telugu": "te-IN",
        "urdu": "ur-PK",
        "spanish": "es-ES",
        "french": "fr-FR",
        "german": "de-DE",
        "italian": "it-IT",
        "portuguese": "pt-BR",
        "dutch": "nl-NL",
        "russian": "ru-RU",
        "arabic": "ar-SA",
        "japanese": "ja-JP",
        "chinese": "zh-CN",
        "korean": "ko-KR",
    }
    return aliases.get(clean, "en-IN")


def validate_audio_file(file_bytes: bytes, filename: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
    """Validate audio file size and extension.

    Returns:
        (is_valid, error_message, extension)
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "Audio file is empty (0 bytes received).", ""

    if len(file_bytes) > MAX_AUDIO_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return False, f"Audio file ({size_mb:.1f} MB) exceeds maximum allowed limit of 10 MB.", ""

    ext = ".wav"
    if filename:
        raw_ext = Path(filename).suffix.lower()
        if raw_ext:
            ext = raw_ext

    if ext not in SUPPORTED_EXTENSIONS:
        return False, (
            f"Unsupported audio format '{ext}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        ), ext

    return True, None, ext


def convert_to_wav(input_path: str, output_path: str) -> bool:
    """Convert audio to 16kHz mono PCM WAV via ffmpeg if available."""
    if not has_ffmpeg():
        return False
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ac", "1", "-ar", "16000",
        "-f", "wav", output_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return res.returncode == 0
    except Exception:
        return False


def transcribe_audio(
    file_bytes: bytes,
    lang: str = "en",
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """Transcribe audio bytes using SpeechRecognition and Google Web Speech API.

    Handles:
    - Input validation (empty, oversized, unsupported extensions).
    - Format conversion for compressed audio where ffmpeg is installed.
    - Safe temporary file management and guaranteed cleanup.
    - Specific error discrimination for silence, corruption, or network failures.
    """
    start_time = time.perf_counter()

    # 1. Validation
    valid, err_msg, ext = validate_audio_file(file_bytes, filename)
    if not valid:
        return {"ok": False, "error": err_msg, "code": "VALIDATION_ERROR"}

    speech_code = get_speech_language(lang)

    # 2. Check dependencies
    try:
        import speech_recognition as sr
    except ImportError:
        return {
            "ok": False,
            "error": "SpeechRecognition library is not installed on this server.",
            "code": "DEPENDENCY_ERROR",
        }

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    temp_files = []
    wav_path = None

    try:
        # Determine whether audio needs conversion
        if ext in NATIVE_EXTENSIONS:
            # Native format: write to temp file or parse directly
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            tmp.write(file_bytes)
            tmp.flush()
            tmp.close()
            temp_files.append(tmp.name)
            wav_path = tmp.name
        else:
            # Non-native format (MP3, M4A, WebM, OGG): requires conversion
            if not has_ffmpeg():
                return {
                    "ok": False,
                    "error": (
                        f"Audio format '{ext}' requires FFmpeg for server-side decoding. "
                        "Please upload a standard WAV, AIFF, or FLAC audio file, or use live browser recording."
                    ),
                    "code": "FFMPEG_REQUIRED",
                }

            in_tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            in_tmp.write(file_bytes)
            in_tmp.flush()
            in_tmp.close()
            temp_files.append(in_tmp.name)

            out_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            out_tmp.close()
            temp_files.append(out_tmp.name)

            converted = convert_to_wav(in_tmp.name, out_tmp.name)
            if not converted or not os.path.exists(out_tmp.name) or os.path.getsize(out_tmp.name) == 0:
                return {
                    "ok": False,
                    "error": f"Failed to decode '{ext}' audio file into playable WAV.",
                    "code": "CONVERSION_ERROR",
                }
            wav_path = out_tmp.name

        # 3. Read and inspect audio source
        try:
            with sr.AudioFile(wav_path) as source:
                duration = source.DURATION or 0.0
                if duration > MAX_AUDIO_DURATION_SEC:
                    return {
                        "ok": False,
                        "error": (
                            f"Audio duration ({duration:.1f}s) exceeds the maximum limit of "
                            f"{int(MAX_AUDIO_DURATION_SEC)} seconds."
                        ),
                        "code": "DURATION_LIMIT_EXCEEDED",
                    }
                audio_data = recognizer.record(source)
        except (ValueError, EOFError, Exception) as read_err:
            return {
                "ok": False,
                "error": f"Could not decode audio data (file may be corrupted or headers malformed): {read_err}",
                "code": "CORRUPTED_AUDIO",
            }

        # 4. Transcribe using Google Speech Recognition
        try:
            text = recognizer.recognize_google(audio_data, language=speech_code)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "ok": True,
                "text": text.strip(),
                "engine": "Google Web Speech API",
                "lang": speech_code,
                "duration_sec": round(duration, 2),
                "latency_ms": round(elapsed_ms, 1),
            }
        except sr.UnknownValueError:
            return {
                "ok": False,
                "error": "No speech could be recognized in the audio. The recording may be silent, low-volume, or unclear.",
                "code": "NO_SPEECH_DETECTED",
            }
        except sr.RequestError as req_err:
            return {
                "ok": False,
                "error": f"Speech recognition service request failed or network unavailable: {req_err}",
                "code": "NETWORK_ERROR",
            }

    finally:
        # 5. Guaranteed cleanup of all temporary files
        for tmp_file in temp_files:
            try:
                if tmp_file and os.path.exists(tmp_file):
                    os.unlink(tmp_file)
            except OSError:
                pass
