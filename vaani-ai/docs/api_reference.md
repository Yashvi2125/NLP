# Vaani AI — REST API Reference Manual

Base URL: `http://localhost:5000` or `https://<your-render-subdomain>.onrender.com`

---

## 1. System Endpoints

### 1.1 Health Check & Operational Metrics
Returns service health, uptime, memory usage, and backend engine status.

- **URL**: `/api/health`
- **Method**: `GET`
- **Headers**: `Accept: application/json`
- **Success Response (HTTP 200)**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_sec": 42.5,
  "memory_mb": 48.2,
  "gemini_configured": true,
  "gemini_model": "gemini-3.1-flash-lite",
  "intent_model_fitted": true,
  "languages_supported": 20,
  "active_sessions": 3
}
```

---

### 1.2 Supported Languages Directory
Lists all supported language metadata, speech recognition tags, and TTS codes.

- **URL**: `/api/languages`
- **Method**: `GET`
- **Success Response (HTTP 200)**:
```json
[
  {
    "code": "hi",
    "name": "Hindi",
    "native": "हिन्दी",
    "speech": "hi-IN",
    "tts": "hi-IN",
    "tier": "core",
    "script": "devanagari"
  },
  {
    "code": "gu",
    "name": "Gujarati",
    "native": "ગુજરાતી",
    "speech": "gu-IN",
    "tts": "gu-IN",
    "tier": "core",
    "script": "gujarati"
  }
]
```

---

## 2. Conversational & NLP Endpoints

### 2.1 Complete NLP Pipeline Analysis (`/api/analyze`)
Processes user text through the full sequential NLP pipeline (Language ID, Preprocessing, Sentiment, NER, Intent Classification, and Conversational Chatbot).

- **URL**: `/api/analyze`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "text": "मेरा नाम राहुल है और मैं मुंबई में रहता हूँ",
  "session_id": "sess-a1b2c3d4e5",
  "reply_to": "auto",
  "translate_to": "en",
  "tz": "Asia/Kolkata"
}
```
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `text` | string | Yes | Raw input string to analyze |
| `session_id` | string | No | Conversational session ID for multi-turn context |
| `reply_to` | string | No | Language code for assistant reply (`"auto"` or e.g. `"hi"`) |
| `translate_to` | string | No | Target language code for translation (default: `"en"`) |
| `tz` | string | No | IANA Timezone string (e.g. `"Asia/Kolkata"`) |

- **Success Response (HTTP 200)**:
```json
{
  "input": "मेरा नाम राहुल है और मैं मुंबई में रहता हूँ",
  "session_id": "sess-a1b2c3d4e5",
  "language": {
    "code": "hi",
    "name": "Hindi",
    "confidence": 0.98,
    "method": "Devanagari Script Analysis",
    "script": "devanagari"
  },
  "preprocessing": {
    "normalized": "मेरा नाम राहुल है और मैं मुंबई में रहता हूँ",
    "tokens": ["मेरा", "नाम", "राहुल", "है", "और", "मैं", "मुंबई", "में", "रहता", "हूँ"],
    "without_stopwords": ["नाम", "राहुल", "मुंबई", "रहता"],
    "stems": ["नाम", "राहुल", "मुंबई", "रहता"],
    "is_mixed": false
  },
  "sentiment": {
    "label": "neutral",
    "compound": 0.0,
    "pos": 0.0,
    "neu": 1.0,
    "neg": 0.0,
    "method": "Multilingual Lexicon",
    "confidence": 0.90
  },
  "intent": {
    "name": "user_intro",
    "confidence": 0.96,
    "ranked": [
      ["user_intro", 0.96],
      ["greeting", 0.02],
      ["fallback", 0.01]
    ]
  },
  "entities": [
    {"type": "PERSON", "value": "राहुल", "confidence": 0.95},
    {"type": "LOCATION", "value": "मुंबई", "confidence": 0.92}
  ],
  "translation": {
    "ok": true,
    "text": "My name is Rahul and I live in Mumbai",
    "target": "en",
    "target_name": "English",
    "engine": "Deep Translator"
  },
  "timing": {
    "local_nlp_ms": 2.14,
    "chatbot_ms": 0.45,
    "total_ms": 2.59
  },
  "reply": {
    "text": "आपसे मिलकर खुशी हुई, राहुल!",
    "english": "Nice to meet you, Rahul!",
    "lang": "hi",
    "tts": "hi-IN",
    "engine": "offline localisation",
    "latency_ms": 0.45
  }
}
```

- **Error Response (HTTP 400)**:
```json
{
  "error": "Empty input"
}
```

---

### 2.2 Audio Transcription (`/api/transcribe`)
Uploads and transcribes audio files using server-side SpeechRecognition with Google Web Speech API.

- **URL**: `/api/transcribe`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `audio`: Audio binary file (`.wav`, `.aiff`, `.flac`, `.mp3`, `.m4a`, `.webm`, `.ogg`)
  - `lang`: Optional language code (default: `"en"`)
  - `auto_analyze`: Optional `"true"` to run through NLP pipeline immediately
  - `session_id`: Optional session ID for conversational memory
- **Success Response (HTTP 200)**:
```json
{
  "ok": true,
  "text": "hello what time is it",
  "engine": "Google Web Speech API",
  "lang": "en-IN",
  "duration_sec": 2.33,
  "latency_ms": 867.1
}
```

- **Validation Error (HTTP 400)**:
```json
{
  "ok": false,
  "error": "Audio file (14.2 MB) exceeds maximum allowed limit of 10 MB.",
  "code": "VALIDATION_ERROR"
}
```

- **Decoding Error / Silence (HTTP 422)**:
```json
{
  "ok": false,
  "error": "No speech could be recognized in the audio. The recording may be silent, low-volume, or unclear.",
  "code": "NO_SPEECH_DETECTED"
}
```

---

### 2.3 Conversation Memory Reset (`/api/chat/reset`)
Purges session history and clears conversational context entities.

- **URL**: `/api/chat/reset`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "session_id": "sess-a1b2c3d4e5"
}
```
- **Success Response (HTTP 200)**:
```json
{
  "ok": true,
  "session_id": "sess-a1b2c3d4e5",
  "cleared": true
}
```

---

### 2.4 Conversation History Inspection (`/api/chat/history`)
Retrieves turn history and extracted context entities for debugging and UI inspection.

- **URL**: `/api/chat/history?session_id=sess-a1b2c3d4e5`
- **Method**: `GET`
- **Success Response (HTTP 200)**:
```json
{
  "ok": true,
  "session_id": "sess-a1b2c3d4e5",
  "history": [
    {
      "role": "user",
      "text": "मेरा नाम राहुल है",
      "lang": "hi",
      "entities": [{"type": "PERSON", "value": "राहुल"}],
      "intent": "user_intro",
      "timestamp": 1794857412.34
    },
    {
      "role": "model",
      "text": "आपसे मिलकर खुशी हुई, राहुल!",
      "lang": "hi",
      "entities": [],
      "intent": null,
      "timestamp": 1794857412.35
    }
  ],
  "context_entities": {
    "person": "राहुल"
  }
}
```

---

## 3. Error Codes Reference

| Error Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `NO_FILE` | 400 | No `audio` file included in multipart request |
| `VALIDATION_ERROR` | 400 | Empty file, unsupported format, or oversized upload (> 10 MB) |
| `PAYLOAD_TOO_LARGE` | 413 | Request payload exceeded maximum 16 MB limit |
| `CORRUPTED_AUDIO` | 422 | Corrupted audio headers or unreadable byte stream |
| `NO_SPEECH_DETECTED` | 422 | Audio is silent or unintelligible |
| `FFMPEG_REQUIRED` | 422 | Compressed format (.mp3/.m4a) uploaded on host lacking ffmpeg |
| `DURATION_LIMIT_EXCEEDED`| 422 | Audio duration exceeded maximum 120-second boundary |
| `MISSING_SESSION_ID` | 400 | `session_id` omitted in request requiring session context |
| `INTERNAL_SERVER_ERROR` | 500 | Unhandled server exception (safely masked without leaking stack traces) |
