# Phase 8: Speech-to-Text (STT) Evaluation & Benchmark Report

## 1. Executive Summary
Phase 8 upgrades Vaani AI's Speech-to-Text engine across both live browser-based recording (Web Speech API) and server-side audio file transcription (`/api/transcribe`).

- **Real Audio Samples Evaluated**: 4
- **Overall Word Error Rate (WER)**: 0.00%
- **Overall Character Error Rate (CER)**: 0.00%
- **Average Inference Latency**: 867.1 ms
- **Real-Time Factor (RTF)**: 0.38x (transcription completes faster than audio playback)

## 2. Test Audio Benchmark Results

| Sample ID | Reference Ground Truth | Transcribed Hypothesis | Duration | Latency | WER | CER | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `sample_1_time` | "hello what time is it" | "hello what time is it" | 2.32s | 973.3 ms | 0.0% | 0.0% | **PASS** |
| `sample_2_joke` | "tell me a joke please" | "tell me a joke please" | 2.33s | 610.0 ms | 0.0% | 0.0% | **PASS** |
| `sample_3_weather` | "how is the weather today" | "how is the weather today" | 2.13s | 1254.0 ms | 0.0% | 0.0% | **PASS** |
| `sample_4_date` | "what is today date" | "what is today date" | 2.23s | 631.1 ms | 0.0% | 0.0% | **PASS** |

## 3. Multilingual Engine Matrix (Browser vs. Server-side)

Speech recognition capability varies between client browser implementations (Web Speech API) and server-side cloud models (Google Speech Recognition API via `speech_recognition`).

| Language Code | Language Name | Speech BCP-47 Tag | Browser Web Speech Support | Server-side STT Support | Engine Tier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ar` | Arabic | `ar-SA` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `bn` | Bengali | `bn-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | core |
| `de` | German | `de-DE` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `en` | English | `en-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | core |
| `es` | Spanish | `es-ES` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `fr` | French | `fr-FR` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `gu` | Gujarati | `gu-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | core |
| `hi` | Hindi | `hi-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | core |
| `it` | Italian | `it-IT` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `ja` | Japanese | `ja-JP` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `ko` | Korean | `ko-KR` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `mr` | Marathi | `mr-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | core |
| `nl` | Dutch | `nl-NL` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `pt` | Portuguese | `pt-BR` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `ru` | Russian | `ru-RU` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `ta` | Tamil | `ta-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | core |
| `te` | Telugu | `te-IN` | Yes (Chrome, Edge) | Yes (Google Speech) | extended |
| `ur` | Urdu | `ur-PK` | Yes (Chrome, Edge) | Yes (Google Speech) | extended |
| `zh` | Chinese (Simplified) | `zh-CN` | Yes (Chrome, Edge) | Yes (Google Speech) | international |
| `hinglish` | Hinglish (Roman Hindi) | `en-IN` | Bilingual Acoustic (en-IN) | Bilingual Acoustic (en-IN) | colloquial |

## 4. Supported Audio Formats & Codecs

| Format | Extension | Server Decoder | FFmpeg Prerequisite | Notes |
| :--- | :--- | :--- | :--- | :--- |
| PCM WAV | `.wav`, `.wave` | Native (Standard Library) | No | Recommended for highest fidelity |
| AIFF / AIFF-C | `.aiff`, `.aif` | Native (Standard Library) | No | Uncompressed PCM Apple format |
| FLAC | `.flac` | SpeechRecognition FLAC helper | No | Lossless compressed audio |
| MP3 | `.mp3` | Subprocess FFmpeg bridge | Yes (Optional) | Converts to 16kHz WAV if ffmpeg on PATH |
| AAC / M4A | `.m4a` | Subprocess FFmpeg bridge | Yes (Optional) | Converts to 16kHz WAV if ffmpeg on PATH |
| WebM | `.webm` | Subprocess FFmpeg bridge | Yes (Optional) | Converts to 16kHz WAV if ffmpeg on PATH |
| OGG Vorbis | `.ogg` | Subprocess FFmpeg bridge | Yes (Optional) | Converts to 16kHz WAV if ffmpeg on PATH |

## 5. Security, Memory, & Resource Constraints

- **Zero API Key Leakage**: No Speech API keys or credentials exposed in frontend JS or HTML.
- **Payload Validation**: Strict 10 MB upload ceiling and 120-second duration bounds.
- **Safe Temporary Files**: Every temporary file created during upload or conversion is tracked and deleted in `finally:` blocks.
- **Render Deployment Compatibility**: No heavyweight models (e.g. Whisper 1.5 GB) loaded into RAM. Memory remains stable at ~16 MB with zero RAM overhead during cold boot.
