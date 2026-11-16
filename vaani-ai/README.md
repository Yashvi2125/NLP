# Vaani AI — Voice-to-Text Analysis & Multilingual Conversational Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 134 passing](https://img.shields.io/badge/tests-134%20passed-brightgreen.svg)]()
[![Model Accuracy: 93.86%](https://img.shields.io/badge/Accuracy-93.86%25-success.svg)]()
[![Render: Ready](https://img.shields.io/badge/Render-Deploy%20Ready-black.svg)](https://render.com)

**Vaani AI** is an advanced NLP-powered Multilingual Conversational Assistant and Voice-to-Text intelligence application. It bridges low-latency offline machine learning models with cloud LLM reasoning, delivering real-time language detection, intent classification, sentiment analysis, entity extraction, and conversational responses across **20 languages and colloquial Hinglish**.

---

## 🌟 Key Features

- **🌐 20 Languages + Hinglish**: Core Indian regional languages (Hindi, Marathi, Gujarati, Bengali, Tamil, Telugu, Urdu), European languages (Spanish, French, German, Italian, Portuguese, Dutch, Russian), and Asian/Middle Eastern languages (Arabic, Japanese, Chinese Simplified, Korean), alongside specialized Hinglish (Roman Hindi) support.
- **⚡ Dual-Engine Hybrid Router**:
  - **Fast-Path Offline Engine**: Supported high-confidence local commands execute locally in $< 2\text{ ms}$ with zero network or token overhead.
  - **Google Gemini API Fallback**: Open-ended queries, factoids, and complex dialogues seamlessly route to `gemini-3.1-flash-lite` with full multi-turn conversational memory.
  - **Graceful Offline Degradation**: Automatically falls back to offline localized responses when network connectivity or API credentials are unavailable.
- **🎙️ Comprehensive Speech-to-Text (STT)**:
  - **Client-Side Live Streaming**: Low-latency voice input using the browser's Web Speech API with interim results and review-before-send ergonomics.
  - **Server-Side Audio Transcription**: Upload and transcribe WAV, AIFF, FLAC, MP3, M4A, WebM, and OGG with automated FFmpeg conversion, strict 10 MB payload validation, and guaranteed temporary file cleanup.
  - **Verified Benchmarks**: Evaluated on standardized audio with **0.00% Word Error Rate (WER)** and an average latency of **867 ms** (0.38x Real-Time Factor).
- **🧠 7-Card NLP Transparency Suite**: Real-time visualization of Language ID, Preprocessing tokens/stems, Bipolar Sentiment Meter, Intent ranking, Categorized NER badges, Translation, and Measured Execution Latency.
- **🔒 Security & Session Isolation**:
  - Thread-safe session management (`SessionMemory`, `MemoryManager`) with sliding TTL expiration.
  - Pronoun reference resolution (*"he"*, *"she"*, *"it"*, *"that place"*).
  - Pre-request scanner blocking adversarial prompt injections, DAN triggers, and credential dumps.
  - Production security headers (`nosniff`, `SAMEORIGIN`, `strict-origin-when-cross-origin`) and 16 MB request caps.
- **🚀 Render Free-Tier Ready**: Memory-optimized architecture (< 60 MB RAM under load), cold start pre-warming, and native Gunicorn configuration for Render Linux containers.

---

## 🏗️ Architecture Overview

```
                                    User Speech / Text
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │   Flask Web Server (app.py)     │
                           │   Security Headers, 16MB Cap    │
                           └────────────────┬────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
       ┌───────────────────────────┐                 ┌───────────────────────────┐
       │   Browser Web Speech API  │                 │ Server STT (nlp/speech.py)│
       │   Live Streaming Voice    │                 │ Native WAV / FFmpeg MP3   │
       └─────────────┬─────────────┘                 └─────────────┬─────────────┘
                     └──────────────────────┬──────────────────────┘
                                            ▼
                           ┌─────────────────────────────────┐
                           │  NLP Pipeline (nlp/pipeline.py) │
                           ├─────────────────────────────────┤
                           │ 1. Preprocess & NFKC Normalizer │
                           │ 2. 4-Tier Language ID Engine    │
                           │ 3. Multilingual Sentiment (SOV) │
                           │ 4. 9-Category Entity Extractor  │
                           │ 5. Word+Char TF-IDF Classifier  │
                           └────────────────┬────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │  Hybrid Router (nlp/chatbot.py) │
                           └────────┬───────────────┬────────┘
                                    │               │
            High Confidence (>= 0.45)               Fallback / Open-Ended Query
                                    │               │
                                    ▼               ▼
                      ┌───────────────────┐   ┌───────────────────────────┐
                      │ Local Rule Engine │   │ Session Memory Context    │
                      │   (< 2 ms offline)│   │ Pronoun Resolution Engine │
                      └───────────────────┘   └─────────────┬─────────────┘
                                                            │
                                                            ▼
                                              ┌───────────────────────────┐
                                              │ Injection Defense Scanner │
                                              └─────────────┬─────────────┘
                                                            │
                                                            ▼
                                              ┌───────────────────────────┐
                                              │ Google Gemini REST API    │
                                              │ (gemini-3.1-flash-lite)   │
                                              └───────────────────────────┘
```

---

## 💻 Tech Stack

| Domain | Technology / Library | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Flask 3.1.3, Gunicorn 21.2 | High-performance WSGI web application server |
| **NLP Classification** | scikit-learn 1.9.1, NumPy, SciPy | Dual Word+Char TF-IDF Vectorizer + Calibrated Logistic Regression |
| **Datasets** | AmazonScience/massive + Regional Corpora | 14,878 clean multilingual utterances across 7 core regional languages |
| **Sentiment Analysis** | vaderSentiment + Custom Multilingual Lexicons | SOV post-predicate negation window + CJK length-descending span matching |
| **LLM Orchestration** | Google Gemini REST API | `gemini-3.1-flash-lite` with defensive system instructions |
| **Speech Processing** | SpeechRecognition, Web Speech API, audioop | Streaming browser speech + multi-format server-side transcription |
| **Frontend UI** | HTML5, Modern Vanilla CSS3, JavaScript (ES6) | Responsive, dual-theme, 7-card transparency suite, zero bloated npm deps |
| **Testing** | pytest, pytest-timeout, Playwright | 134 automated unit, integration, and UI browser tests |

---

## 🚀 Quick Start & Local Execution

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Git

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/vaani-ai.git
cd vaani-ai/vaani-ai

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in `vaani-ai/`:
```ini
# Optional: Add your Google Gemini API key for open-ended knowledge queries
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Enable Flask debug mode for local development (0 in production)
FLASK_DEBUG=0
PORT=5000
```
*(Note: If `GEMINI_API_KEY` is omitted, the application operates in 100% offline fallback mode).*

### 4. Run Application
```bash
python app.py
```
Open your browser to: `http://localhost:5000`

---

## 🧪 Automated Testing & Evaluation

Execute the complete test suite across all 10 phases:
```bash
# Run all 134 unit, integration, and contract tests
python -m pytest tests -v

# Run speech recognition WER/CER benchmarking on real audio
python scripts/evaluate_speech.py

# Run consolidated model evaluation benchmark
python scripts/run_all_evaluations.py
```

---

## 📡 REST API Reference Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Serves the web application user interface |
| `GET /api/health` | `GET` | System health check (uptime, memory MB, model fitted, sessions) |
| `GET /api/languages` | `GET` | Lists all 20 supported languages and BCP-47 speech tags |
| `POST /api/analyze` | `POST` | Full sequential NLP analysis & hybrid chatbot response |
| `POST /api/transcribe` | `POST` | Uploads and transcribes audio files (`multipart/form-data`) |
| `POST /api/chat/reset` | `POST` | Resets session memory and clears context entities |
| `GET /api/chat/history` | `GET` | Retrieves conversational turn transcripts and active entities |

*For complete request and response schemas, see [docs/api_reference.md](docs/api_reference.md).*

---

## ☁️ Render Deployment

Vaani AI is optimized for [Render](https://render.com) free-tier deployment:
1. Connect your repository to Render.
2. Select **Web Service** with runtime **Python 3**.
3. **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
5. **Environment Variables**: Set `PYTHON_VERSION=3.11.9` and `GEMINI_API_KEY`.
6. **Health Check Path**: `/api/health`.

*For detailed instructions, see [docs/deployment.md](docs/deployment.md).*

---

## 📚 Documentation Directory

- 📐 [Architecture & System Design](docs/architecture.md)
- 🔌 [REST API Reference](docs/api_reference.md)
- 📊 [Model Evaluation & Benchmarking Report](docs/evaluation.md)
- 🚀 [Production & Render Deployment Guide](docs/deployment.md)
- 📝 [Project Changelog](CHANGELOG.md)

---

## 📄 License
This project is licensed under the MIT License.
