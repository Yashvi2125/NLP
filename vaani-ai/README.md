# VaaniAI – Voice-to-Text Analysis & Multilingual Conversational Assistant
NLP Major Project #10. Speak/type in Hindi, Hinglish, English, Marathi, Gujarati, Bengali, Tamil, Spanish, French or German.
The app detects the language, preprocesses the text, analyses sentiment, classifies intent, extracts entities, translates, and replies (text + speech) in your language.

## Run
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py            # open http://localhost:5000  (use Chrome/Edge for the microphone)
pytest -q                # 31 tests
python evaluate.py       # metrics for the report
```

## NLP pipeline (maps to syllabus)
| Stage | File | Technique |
|---|---|---|
| Speech-to-text | `static/app.js`, `nlp/speech.py` | Web Speech API (live), SpeechRecognition (WAV upload) |
| Preprocessing | `nlp/preprocess.py` | Unicode normalisation, tokenisation, stop-words, stemming |
| Language ID | `nlp/langid.py` | Unicode-script rules + langdetect (n-gram Naive Bayes) + Hinglish heuristic |
| Sentiment | `nlp/sentiment.py` | VADER; translate→VADER; offline multilingual lexicon |
| Intent | `nlp/intent.py` | Word+char TF-IDF + Logistic Regression (15 intents, 467 utterances) |
| NER | `nlp/intent.py` | Rule/regex + gazetteer: PERSON, CITY, LANGUAGE, TIME, DATE, PHONE, EMAIL, NUMBER |
| Translation | `nlp/translate.py` | Google (online) with offline phrasebook fallback |
| Chatbot | `nlp/chatbot.py` | Intent → template reply → localised; sentiment refines sad/happy |

## Known limitations (state these honestly in the report)
- Live microphone uses the browser's speech engine (Chrome/Edge, needs internet).
- Translation of free-form sentences needs internet; offline mode only covers the phrasebook.
- Intent 5-fold CV accuracy ≈ 0.68 on a small multilingual dataset (more data = better).
- Hinglish detection is heuristic; NER is rule-based.
