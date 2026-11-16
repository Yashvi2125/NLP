# Vaani AI — Model Training & Evaluation Report

## 1. Executive Summary

This evaluation benchmarks the **Existing Baseline Model** (TF-IDF 1-2 word / 2-4 char + Logistic Regression) against the **Improved Calibrated Model** (Subword 2-5 char / 1-3 word TF-IDF with sublinear scaling + Calibrated Linear Classifier) on the strictly held-out, unseen test partition (2,555 utterances across English, Hindi, Bengali, Tamil, Marathi, Gujarati, and Hinglish).

## 2. Model Performance Comparison

| Metric | Baseline Model | Improved Calibrated Model | Delta |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | **93.86%** | 92.52% | -1.33% |
| **Macro Precision** | **86.90%** | 85.08% | -1.81% |
| **Macro Recall** | **80.47%** | 71.86% | -8.61% |
| **Macro F1 Score** | **82.99%** | 77.06% | -5.93% |
| **Weighted F1 Score** | **93.82%** | 92.31% | -1.51% |

## 3. Per-Intent Detailed Breakdown (Champion Model)

| Intent Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `about_project` | 80.0% | 80.0% | 80.0% | 10 |
| `alarm_query` | 95.3% | 91.0% | 93.1% | 133 |
| `alarm_set` | 92.0% | 94.3% | 93.2% | 159 |
| `ask_date` | 91.2% | 93.3% | 92.2% | 89 |
| `ask_name` | 60.0% | 75.0% | 66.7% | 8 |
| `ask_time` | 96.2% | 89.7% | 92.8% | 223 |
| `capabilities` | 87.5% | 63.6% | 73.7% | 11 |
| `compliment` | 100.0% | 75.0% | 85.7% | 8 |
| `goodbye` | 100.0% | 63.6% | 77.8% | 11 |
| `greeting` | 60.0% | 60.0% | 60.0% | 15 |
| `happy` | 57.1% | 36.4% | 44.4% | 11 |
| `joke` | 94.1% | 86.5% | 90.1% | 74 |
| `music` | 97.6% | 96.3% | 96.9% | 674 |
| `qa_factoid` | 89.5% | 97.2% | 93.2% | 541 |
| `sad` | 53.8% | 63.6% | 58.3% | 11 |
| `thanks` | 100.0% | 81.8% | 90.0% | 11 |
| `translate_request` | 100.0% | 85.7% | 92.3% | 7 |
| `user_intro` | 100.0% | 100.0% | 100.0% | 9 |
| `weather` | 96.7% | 95.8% | 96.3% | 550 |

## 4. Key Architectural Takeaways

1. **Baseline Champion Performance**: Word (1-2) + Char (2-4) TF-IDF paired with class-weighted Logistic Regression (C=12) achieved a dominant **93.86% Accuracy** and **82.99% Macro F1**.
2. **Under-Represented Class Sensitivity**: In small conversational classes (`translate_request`, `user_intro`, `compliment`), full-dataset balanced cross-entropy in Logistic Regression outperformed 3-fold internal calibration splits which starved minority classes.
3. **Zero Startup Latency**: Training is completely decoupled from Flask boot. The application loads the serialized pipeline artifact instantly (< 0.05 seconds).
4. **Memory Footprint**: The complete serialized pipeline is ~15 MB, well within Render's free tier (512 MB memory limit).