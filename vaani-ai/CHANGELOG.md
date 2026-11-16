# Changelog — Vaani AI

All notable changes and architectural upgrades across the development roadmap are documented here.

---

## [Post-Phase 10 Bugfix] - Production Hotfixes & Multilingual Enhancements
### Fixed
- **Gemini API Failure & Model Support**:
  - Replaced unsupported and deprecated model identifiers with validated production models (`gemini-3.5-flash-lite`, `gemini-flash-lite-latest`, `gemini-3-flash-preview`, `gemini-3.5-flash`).
  - Added structured diagnostic error logging (`logging.getLogger("vaani.gemini")`) that distinguishes between `auth_error` (HTTP 401/403), `model_not_found` (HTTP 404), `rate_limited` (HTTP 429), `service_unavailable` (HTTP 503), `timeout`, and `network_error` without exposing API keys or sensitive data.
  - Aligned frontend badges (`formatEngineBadge`) across chat bubbles and the Insights header to accurately identify `Gemini AI`, `Local Engine`, and `Offline Fallback`.
- **Sentiment Analysis NaN Bug**:
  - Fixed zero-denominator component calculations when processing neutral texts or non-English inputs lacking sentiment lexicon tokens (such as Tamil: `உங்கள் பெயர் என்ன`).
  - Guaranteed finite proportions for `pos`, `neu`, and `neg` summing strictly to 1.0 (100%) across all languages.
  - Implemented safe frontend parsing fallback (`Number.isFinite()`) in `static/app.js` to prevent any `NaN%` display even if upstream data is undefined or null.
- **Translation Command Parsing**:
  - Re-architected translation parser in `nlp/chatbot.py` to support prepositions `to`, `in`, and `into` (e.g. `translate good morning to Hindi` vs. `translate good morning in Hindi`).
  - Implemented fuzzy language name resolution (`resolve_target_language`) with a conservative 0.80 similarity cutoff against full names (>= 4 chars), cleanly correcting common typos like `gujararti` -> `gujarati` while guarding against vocabulary false positives (e.g. `car`).
  - Added multi-tier translation fallback (curated verified phrasebook -> Google Translate -> MyMemory API -> offline phrasebook) and extended curated phrases to include `"i'm eating"`, `"i am eating"`.
- **Multilingual Local Conversational Fallback**:
  - Added native conversational intent rules (`ask_name`, `capabilities`, `how_are_you`, `greeting`, `thanks`, `goodbye`) covering Tamil, Gujarati, Hindi, Marathi, Bengali, Hinglish, and English.
  - Added complete native localized responses in `nlp/localized.py` for Tamil (`ta`), Bengali (`bn`), and Hinglish (`hinglish`), as well as `how_are_you` in all languages.
  - Prioritized command keywords to ensure combined phrases (e.g., `"Hello, what is the time right now?"`) route to the proper command intent (`ask_time`) rather than truncating to greeting.

### Added
- Automated bugfix and regression test suite (`tests/test_bugfixes.py`) with 16 comprehensive unit and integration tests (mocked external calls, zero API quota cost).
- Detailed audit and root cause report: `reports/post_phase10_bugfix_report.md`.

---

## [Phase 10] - Complete System Integration, Security Audit, & Render Deployment Readiness
### Added
- Health-check monitoring endpoint (`/api/health`) returning uptime, memory consumption, model state, and active sessions.
- Security headers middleware (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`).
- Request payload ceiling (`MAX_CONTENT_LENGTH = 16MB`) with custom JSON 413 handler.
- Gunicorn configuration and Render deployment blueprint (`Procfile`, `render.yaml`).
- Comprehensive documentation suite: `docs/architecture.md`, `docs/api_reference.md`, `docs/evaluation.md`, `docs/deployment.md`.
- Automated Phase 10 integration and concurrency test suite (`tests/test_phase10_integration.py`).

---

## [Phase 9] - Frontend Refinement & User Experience
### Added
- Complete 7-card NLP Transparency Suite:
  1. Language Identification (confidence bar, native script name, detection method).
  2. Preprocessing & Script Normalization (tokens, stopwords removed, stems, mixed scripts).
  3. Sentiment Analysis & Polarity (bipolar valence slider -1.0 to +1.0, emoji indicator, component breakdown).
  4. Intent Classification (clean Title Case names, confidence bar, ranked alternatives).
  5. Named Entity Recognition (color-coded categorized pill badges: Person, Location, Org, Date/Time, Contact, Numeric).
  6. Processing Latency & Transparency (non-fabricated latency metrics, stacked visual bar, engine origin badge).
  7. Translation & Speech Output (target language, translated text, TTS code).
- Real-time animated typing indicator (`.typing-dots`) during pipeline and API generation.
- Chat message timestamps and input source badges (`⌨️ Text`, `🎙️ Voice`, `📎 Audio file`).
- Mobile responsive dual-tab switcher (`💬 Chat` vs. `🧠 NLP Insights`) on screens $\le 900\text{ px}$.
- Accessible focus states (`:focus-visible`) and WCAG AA contrast compliance.
- Automated UI screenshot capture script (`scripts/capture_screenshots.py`) using Playwright.

---

## [Phase 8] - Speech-to-Text (STT) Enhancements
### Added
- Upgraded Web Speech API browser live streaming with `event.resultIndex` transcript segregation (eliminating duplicate word concatenation).
- Review-before-send workflow and optional "Auto-send voice" toggle.
- Server-side audio file transcription (`/api/transcribe`) supporting WAV, AIFF, FLAC, MP3, M4A, WebM, and OGG.
- Subprocess FFmpeg bridge for compressed audio decoding with graceful fallback alerts when uninstalled.
- BCP-47 speech recognition code resolution for all 20 languages and Hinglish.
- Audio benchmarking script (`scripts/evaluate_speech.py`) computing Word Error Rate (WER) and Character Error Rate (CER).
- Automated Phase 8 test suite (`tests/test_phase8_speech.py`).

---

## [Phase 7] - Conversational Chatbot (Hybrid Router + Gemini Fallback + Multi-Turn Memory)
### Added
- Hybrid routing architecture:
  - Fast-path local rule engine for high-confidence intents ($\ge 0.45$) executing in $< 2\text{ ms}$ offline.
  - Google Gemini API fallback (`gemini-3.1-flash-lite`) for open-ended queries, factoids, and general conversation.
- Secure REST client (`nlp/gemini_client.py`) with zero API key leakage and 10.0s strict timeouts.
- Pre-request adversarial scanner rejecting prompt injections, DAN triggers, and credential dumps.
- Thread-safe session memory manager (`nlp/memory.py`) with FIFO sliding turn limit and 1-hour TTL expiration.
- Pronoun reference resolution (*"he"*, *"she"*, *"it"*, *"that place"*) injecting entity context into multi-turn payloads.
- Flask endpoints `/api/chat/reset` and `/api/chat/history`.

---

## [Phase 6] - Model Evaluation Report & Comparative Benchmarking
### Added
- Consolidated benchmark evaluation suite across all NLP modules (`scripts/run_all_evaluations.py`).
- Scientific comparative evaluation against naive baselines.
- Memory and latency profiling under concurrent requests.
- Markdown report: `reports/consolidated_model_evaluation_report.md`.

---

## [Phase 5] - Named Entity Recognition (NER)
### Added
- 9-category entity extractor (`nlp/ner.py`): `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE`, `TIME`, `PHONE`, `EMAIL`, `MONEY`, `NUMBER`.
- SOV copula stripping (*है, आहे, છે, ہے*) in Indic names.
- Universal Latin Title Case guarding preventing false-positive name classifications on casual words.
- CJK full-width punctuation stripping and multi-word location gazetteers.

---

## [Phase 4] - Sentiment Analysis
### Added
- Multilingual sentiment engine (`nlp/sentiment.py`) supporting all 20 target languages.
- Native English VADER integration.
- Bidirectional SOV negation window detecting negated predicates (*नहीं, नाही, નથી, nahi*).
- CJK length-descending span matching and universal emoji valence scoring.

---

## [Phase 3] - Language Identification & Registry Expansion
### Added
- Expanded language registry (`nlp/languages.py`) to 20 target languages + Hinglish.
- 4-tier hierarchical detection engine (`nlp/langid.py`): script routing, Devanagari Hindi vs. Marathi marker routing, and Latin Hinglish vs. European lexicon routing.
- Benchmark: 100.0% accuracy across 85 test utterances (vs. 83.5% for naive `langdetect`).

---

## [Phase 2] - Multilingual Preprocessing & Script Normalization
### Added
- Production-grade text normalizer (`nlp/preprocess.py`) preserving original input while creating a normalized copy.
- Unicode NFKC normalization and Indian punctuation / danda handling (`।`, `॥`).
- Hinglish phonetic normalizer mapping Roman Hindi spellings to standard phonetic equivalents.
- Preserved Indic root words intact after empirical testing proved aggressive suffix stemming degrades intent accuracy.

---

## [Phase 1] - Dataset Curation & Intent Classifier Training
### Added
- Curated Amazon MASSIVE subsets (`en`, `hi`, `bn`, `ta`) merged with regional corpora (`gu`, `mr`, `hinglish`) totaling 14,878 clean samples.
- Trained champion model: Word (1-2) + Character (3-5) TF-IDF Vectorizer with calibrated Logistic Regression (`C=12.0`).
- Accuracy: **93.86%**, Macro F1: **82.99%** on held-out test split (2,555 samples). Saved to `models/intent_model.joblib`.
- Zero training at Flask startup.
