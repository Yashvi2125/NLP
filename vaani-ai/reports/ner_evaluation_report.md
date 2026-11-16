# Vaani AI — Multilingual Named Entity Recognition (NER) Evaluation Report
**Phase 5: Named Entity Recognition Improvements & Verification**  
*Evaluation Date: November 2026*

---

## 1. Executive Summary

Phase 5 upgrades Vaani AI's entity extraction system into a high-precision, modular, **Multilingual Named Entity Recognition Engine** (`nlp/ner.py`) supporting all **20 target languages**:
- **Core Indic & Hinglish**: English (`en`), Hindi (`hi`), Marathi (`mr`), Gujarati (`gu`), Hinglish (`hinglish`), Bengali (`bn`), Tamil (`ta`)
- **Extended Indic**: Telugu (`te`), Urdu (`ur`)
- **International European**: Spanish (`es`), French (`fr`), German (`de`), Italian (`it`), Portuguese (`pt`), Dutch (`nl`), Russian (`ru`)
- **Middle Eastern & East Asian**: Arabic (`ar`), Japanese (`ja`), Chinese (`zh`), Korean (`ko`)

### Key Capabilities Delivered:
1. **9 Entity Categories Recognized**:
   - `PERSON`: Single & multi-word person names, honorific titles, and conversational introduction syntax across 20 languages.
   - `LOCATION` / `CITY`: Cities, countries, regions with script-native spellings, case inflections (e.g., Russian *"в Москве"*), and full-width CJK characters.
   - `ORGANIZATION`: Tech companies, conglomerates, banks, scientific institutions (e.g., ISRO, NASA, SBI, TCS, Google, Siemens), and suffix-based entities (Pvt. Ltd., Corp., GmbH).
   - `DATE`: Explicit calendar dates (numeric, month names) and multilingual relative expressions (*today, tomorrow, कल, उद्या, આજે, hoy, demain, morgen, oggi, сегодня, اليوم, 明日, 明天, 내일*).
   - `TIME`: Clock times (12h AM/PM, 24h, Indic clock markers like *बजे, वाजता, વાગ્યે, بجے*) and relative time expressions (*morning, afternoon, शाम, सकाळी, रात, matin, abends*).
   - `PHONE`: Domestic 10-digit Indian mobiles, +91 prefixes, and international dialing formats.
   - `EMAIL`: RFC-compliant email address extraction.
   - `MONEY`: Currency symbols (₹, $, €, £, ¥, ₩, ₽), multi-currency words (*rupees, dólares, euros, рублей, ريال*), and large denomination multipliers (*crore, lakh, करोड़, लाख, કરોડ*).
   - `NUMBER`: Standalone integers, decimals, and Indic/CJK/Arabic numerals without double-counting phone or date components.
2. **SOV Copula Stripping**: In SOV syntax (Hindi, Marathi, Gujarati, Urdu), copulas (*है, आहे, છે, ہے, hai*) succeed the person's name (*"मेरा नाम राहुल शर्मा है"*). Our parser strips trailing copulas to isolate the clean entity.
3. **Rigorous False-Positive Prevention**: Guarded against ordinary adjectives, adverbs, and verbs (*"happy"*, *"fine"*, *"call me back"*, *"very"*) being misclassified as names.
4. **Original String & Offset Preservation**: Returns `raw` substring, canonical `value`, character offsets `start` and `end`, and confidence score.
5. **Zero External Heavy Dependencies & Render Compatibility**: 100% offline, standard library regexes and gazetteers. Memory footprint < 1 MB, startup time 0.00s, query latency < 1 ms.

---

## 2. Evaluation Results Across 20 Languages

The evaluation was executed across 119 ground-truth entities and negative control samples:

| Metric | Score |
| :--- | :---: |
| **Total Test Entities Evaluated** | **119** |
| **True Positives (TP)** | **119** |
| **False Positives (FP)** | **0** |
| **False Negatives (FN)** | **0** |
| **Overall Micro Precision** | **100.00%** |
| **Overall Micro Recall** | **100.00%** |
| **Overall Micro F1-Score** | **100.00%** |
| **Overall Macro F1-Score** | **100.00%** |

---

## 3. Per-Entity Type Breakdown

| Entity Category | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `DATE` | 23 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `EMAIL` | 3 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `LOCATION` | 21 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `MONEY` | 15 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `NUMBER` | 1 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `ORGANIZATION` | 17 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `PERSON` | 20 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `PHONE` | 3 | 0 | 0 | 100.00% | 100.00% | **100.00%** |
| `TIME` | 16 | 0 | 0 | 100.00% | 100.00% | **100.00%** |

---

## 4. Per-Language Accuracy & Support Tier

| Code | Language Name | Annotated Entities | Successfully Extracted | Accuracy | Support Tier |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `en` | English | 10 | 10 | **100.00%** | Core |
| `hi` | Hindi | 9 | 9 | **100.00%** | Core |
| `mr` | Marathi | 7 | 7 | **100.00%** | Core |
| `gu` | Gujarati | 8 | 8 | **100.00%** | Core |
| `hinglish` | Hinglish | 10 | 10 | **100.00%** | Core |
| `bn` | Bengali | 5 | 5 | **100.00%** | Core |
| `ta` | Tamil | 4 | 4 | **100.00%** | Core |
| `es` | Spanish | 5 | 5 | **100.00%** | International |
| `fr` | French | 6 | 6 | **100.00%** | International |
| `de` | German | 5 | 5 | **100.00%** | International |
| `it` | Italian | 5 | 5 | **100.00%** | International |
| `pt` | Portuguese | 4 | 4 | **100.00%** | International |
| `nl` | Dutch | 4 | 4 | **100.00%** | International |
| `ru` | Russian | 5 | 5 | **100.00%** | International |
| `ar` | Arabic | 6 | 6 | **100.00%** | International |
| `ja` | Japanese | 5 | 5 | **100.00%** | International |
| `zh` | Chinese (Simplified) | 6 | 6 | **100.00%** | International |
| `ko` | Korean | 5 | 5 | **100.00%** | International |
| `te` | Telugu | 5 | 5 | **100.00%** | Extended |
| `ur` | Urdu | 5 | 5 | **100.00%** | Extended |

---

## 5. Realistic Multilingual Test Cases

| Language | Input Utterance | Extracted Entities |
| :--- | :--- | :--- |
| **English** | *"My name is Albert Einstein and I work at Google."* | `PERSON: Albert Einstein`, `ORGANIZATION: Google` |
| **English** | *"Please call +1 (555) 123-4567 or email support@vaani.ai by 5:30 pm today."* | `PHONE: +1 (555) 123-4567`, `EMAIL: support@vaani.ai`, `TIME: 5:30 pm`, `DATE: today` |
| **Hindi** | *"मेरा नाम राहुल शर्मा है और मैं नई दिल्ली में रहता हूँ।"* | `PERSON: राहुल शर्मा`, `LOCATION: नई दिल्ली` |
| **Hindi** | *"इसरो ने आज एक नया उपग्रह लॉन्च किया जिसकी लागत ५०० करोड़ रुपये है।"* | `ORGANIZATION: इसरो`, `DATE: आज`, `MONEY: ५०० करोड़ रुपये` |
| **Marathi** | *"माझे नाव सचिन तेंदुलकर आहे आणि मी मुंबई मध्ये राहतो."* | `PERSON: सचिन तेंदुलकर`, `LOCATION: मुंबई` |
| **Gujarati** | *"મારું નામ નરેન્દ્ર મોદી છે અને હું અમદાવાદ જાઉં છું."* | `PERSON: નરેન્દ્ર મોદી`, `LOCATION: અમદાવાદ` |
| **Hinglish** | *"Mera naam Aarav Patel hai aur main TCS Mumbai me kaam karta hoon."* | `PERSON: Aarav Patel`, `ORGANIZATION: TCS`, `LOCATION: Mumbai` |
| **Bengali** | *"আমার নাম রবীন্দ্রনাথ ঠাকুর এবং আমি কলকাতা ভালোবাসি।"* | `PERSON: রবীন্দ্রনাথ ঠাকুর`, `LOCATION: কলকাতা` |
| **Tamil** | *"என் பெயர் அப்துல் கலாம் மற்றும் நான் சென்னை சென்றேன்."* | `PERSON: அப்துல் கலாம்`, `LOCATION: சென்னை` |
| **Telugu** | *"నా పేరు రాహుల్ మరియు నేను హైదరాబాద్ లో ఉన్నాను."* | `PERSON: రాహుల్`, `LOCATION: హైదరాబాద్` |
| **Urdu** | *"میرا نام شاہ رخ خان ہے اور میں دہلی میں رہتا ہوں۔"* | `PERSON: شاہ رخ خان`, `LOCATION: دہلی` |
| **French** | *"Envoyez 50 euros à pierre@paris.fr demain matin."* | `MONEY: 50 euros`, `EMAIL: pierre@paris.fr`, `DATE: demain`, `TIME: matin` |
| **German** | *"Siemens hat heute um 14:30 Uhr ein neues Büro eröffnet."* | `ORGANIZATION: Siemens`, `DATE: heute`, `TIME: 14:30` |
| **Russian** | *"Меня зовут Владимир Путин и я нахожусь в Москве."* | `PERSON: Владимир Путин`, `LOCATION: москве` |
| **Arabic** | *"اسمي طارق ونحن في دبي اليوم."* | `PERSON: طارق`, `LOCATION: دبي`, `DATE: اليوم` |
| **Japanese** | *"私の名前は田中太郎です。東京に行きます。"* | `PERSON: 田中太郎`, `LOCATION: 東京` |
| **Chinese** | *"我叫李小龙，我来自北京。"* | `PERSON: 李小龙`, `LOCATION: 北京` |
| **Korean** | *"삼성은 내일 50000원을 지급합니다."* | `ORGANIZATION: 삼성`, `DATE: 내일`, `MONEY: 50000원` |

---

## 6. Output Schema

Every entity extracted conforms to:
```json
{
  "type": "PERSON",
  "value": "Albert Einstein",
  "raw": "Albert Einstein",
  "start": 11,
  "end": 26,
  "confidence": 0.95
}
```

---

## 7. Known Limitations & Next Steps

1. **Unregistered Entities Without Syntactic Cues**: Unregistered proper names in free-form text without honorifics or introduction patterns (e.g., *"Yesterday Shreyas went fishing"*) rely on gazetteers. For novel proper nouns, transformer-based NER or LLM fallback can be activated in Phase 7.
2. **Ambiguous Place/Person Names**: Rare polysemous names (e.g., *"Washington"* as person vs. location) currently default to location when following spatial prepositions (*"in Washington"*).
