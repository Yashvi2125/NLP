# Audio Fixtures for Vaani AI Speech-to-Text Testing

This directory holds sample audio clips used for live integration testing of the Sarvam AI Speech-to-Text (`/api/stt`) service.

## Recommended Audio Clips

1. `sample_hindi.wav` or `sample_hindi.webm`: Short recording in Hindi (e.g. saying *"नमस्ते, आप कैसे हैं?"*).
2. `sample_gujarati.wav` or `sample_gujarati.webm`: Short recording in Gujarati (e.g. saying *"કેમ છો?"*).
3. `sample_english.wav` or `sample_english.webm`: Short recording in English (e.g. saying *"What is the time?"*).

## How to Record and Add Clips

1. Use Windows Voice Recorder, Audacity, or browser MediaRecorder.
2. Export as 16 kHz mono or stereo WAV or WebM (under 10 seconds, under 1 MB).
3. Place the file in this folder (`tests/fixtures/audio/<filename>`).
4. Live tests in `tests/test_stt.py` automatically look for files in this directory when `SARVAM_API_KEY` is present in your environment.
