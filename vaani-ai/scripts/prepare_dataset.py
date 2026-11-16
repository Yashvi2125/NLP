"""Dataset preparation and harmonization script for Vaani AI.

- Downloads and caches official Amazon MASSIVE splits (en-US, hi-IN, bn-BD, ta-IN).
- Maps MASSIVE intent taxonomy into Vaani AI canonical intents.
- Ingests custom datasets: data/intents.json, data/intents_mr_gu.json, data/curated_regional.json.
- Enforces strict train/validation/test isolation with zero data leakage.
- Generates data/processed/{train,val,test}.json and summary statistics.
"""

import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path
import requests
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache_massive"
PROCESSED_DIR = DATA_DIR / "processed"

LOCALES = {
    "en-US": "en",
    "hi-IN": "hi",
    "bn-BD": "bn",
    "ta-IN": "ta",
}

MASSIVE_INTENT_MAP = {
    "general_greet": "greeting",
    "general_joke": "joke",
    "weather_query": "weather",
    "alarm_set": "alarm_set",
    "alarm_query": "alarm_query",
    "play_music": "music",
    "qa_factoid": "qa_factoid",
}

DATE_REGEX = re.compile(
    r"(?:date|day|today|month|year|tareekh|tarikh|din|वार|दिनांक|तिथी|তারিখ|দিন|தேதி|நாள்)",
    re.IGNORECASE | re.UNICODE,
)


def normalize_text(text: str) -> str:
    """Normalize unicode and whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def download_massive_split(locale: str, split: str) -> Path:
    """Download and cache MASSIVE split jsonl."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_file = CACHE_DIR / f"{locale}_{split}.jsonl"
    if target_file.exists() and target_file.stat().st_size > 0:
        return target_file

    url = f"https://huggingface.co/datasets/SetFit/amazon_massive_intent_{locale}/raw/main/{split}.jsonl"
    print(f"Downloading {locale} {split} from {url}...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    target_file.write_text(resp.text, encoding="utf-8")
    return target_file


def process_massive() -> tuple[list[dict], list[dict], list[dict]]:
    """Download, filter, and map MASSIVE data for all locales."""
    splits_data = {"train": [], "validation": [], "test": []}

    for locale, lang_code in LOCALES.items():
        for split in ("train", "validation", "test"):
            path = download_massive_split(locale, split)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    raw_intent = item.get("label_text", "")
                    utt = normalize_text(item.get("text", ""))
                    if not utt:
                        continue

                    canonical_intent = None
                    if raw_intent in MASSIVE_INTENT_MAP:
                        canonical_intent = MASSIVE_INTENT_MAP[raw_intent]
                    elif raw_intent == "datetime_query":
                        canonical_intent = "ask_date" if DATE_REGEX.search(utt) else "ask_time"

                    if canonical_intent:
                        splits_data[split].append({
                            "text": utt,
                            "intent": canonical_intent,
                            "lang": lang_code,
                            "source": f"massive_{locale}",
                        })

    return splits_data["train"], splits_data["validation"], splits_data["test"]


def load_custom_datasets() -> list[dict]:
    """Load existing custom datasets and regional additions."""
    custom_records = []

    # 1. Base intents.json
    base_file = DATA_DIR / "intents.json"
    if base_file.exists():
        with open(base_file, "r", encoding="utf-8") as f:
            base_data = json.load(f)
            for intent, utts in base_data.items():
                for utt in utts:
                    norm = normalize_text(utt)
                    if norm:
                        custom_records.append({
                            "text": norm,
                            "intent": intent,
                            "lang": "custom",
                            "source": "intents.json",
                        })

    # 2. Existing Marathi & Gujarati dataset
    mr_gu_file = DATA_DIR / "intents_mr_gu.json"
    if mr_gu_file.exists():
        with open(mr_gu_file, "r", encoding="utf-8") as f:
            mr_gu_data = json.load(f)
            for intent, utts in mr_gu_data.items():
                for utt in utts:
                    norm = normalize_text(utt)
                    if norm:
                        custom_records.append({
                            "text": norm,
                            "intent": intent,
                            "lang": "mr_gu",
                            "source": "intents_mr_gu.json",
                        })

    # 3. New curated regional additions (Hinglish, Marathi, Gujarati)
    regional_file = DATA_DIR / "curated_regional.json"
    if regional_file.exists():
        with open(regional_file, "r", encoding="utf-8") as f:
            reg_data = json.load(f)
            for intent, lang_dict in reg_data.items():
                for lang, utts in lang_dict.items():
                    for utt in utts:
                        norm = normalize_text(utt)
                        if norm:
                            custom_records.append({
                                "text": norm,
                                "intent": intent,
                                "lang": lang,
                                "source": "curated_regional.json",
                            })

    return custom_records


def split_custom_data(records: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Stratified split of custom records into train (70%), val (15%), test (15%)."""
    labels = [r["intent"] for r in records]

    # Split train vs temp (85% vs 15% or 70% vs 30%)
    train_records, temp_records = train_test_split(
        records, test_size=0.30, random_state=42, stratify=labels
    )
    temp_labels = [r["intent"] for r in temp_records]
    val_records, test_records = train_test_split(
        temp_records, test_size=0.50, random_state=42, stratify=temp_labels
    )
    return train_records, val_records, test_records


def deduplicate_and_prevent_leakage(train: list[dict], val: list[dict], test: list[dict]):
    """Ensure zero data leakage between train, val, and test splits."""
    def to_key(utt: str) -> str:
        return re.sub(r"[^\w\s]", "", utt.lower().strip())

    train_keys = {}
    cleaned_train = []
    for r in train:
        k = to_key(r["text"])
        if k and k not in train_keys:
            train_keys[k] = r["intent"]
            cleaned_train.append(r)

    val_keys = set()
    cleaned_val = []
    for r in val:
        k = to_key(r["text"])
        # No overlap with train and no duplicate in val
        if k and k not in train_keys and k not in val_keys:
            val_keys.add(k)
            cleaned_val.append(r)

    test_keys = set()
    cleaned_test = []
    for r in test:
        k = to_key(r["text"])
        # No overlap with train or val, and no duplicate in test
        if k and k not in train_keys and k not in val_keys and k not in test_keys:
            test_keys.add(k)
            cleaned_test.append(r)

    return cleaned_train, cleaned_val, cleaned_test


def main():
    print("=" * 60)
    print("Vaani AI - Dataset Preparation & Taxonomy Harmonization")
    print("=" * 60)

    # Step 1: MASSIVE processing
    print("\n[1/4] Processing Amazon MASSIVE dataset (en-US, hi-IN, bn-BD, ta-IN)...")
    m_train, m_val, m_test = process_massive()
    print(f"MASSIVE filtered items -> Train: {len(m_train)}, Val: {len(m_val)}, Test: {len(m_test)}")

    # Step 2: Custom datasets processing
    print("\n[2/4] Processing custom datasets & regional curation...")
    custom_records = load_custom_datasets()
    print(f"Loaded {len(custom_records)} custom utterances from JSON sources.")
    c_train, c_val, c_test = split_custom_data(custom_records)
    print(f"Custom split -> Train: {len(c_train)}, Val: {len(c_val)}, Test: {len(c_test)}")

    # Step 3: Combine and isolate
    print("\n[3/4] Merging and applying leakage prevention & deduplication...")
    raw_train = m_train + c_train
    raw_val = m_val + c_val
    raw_test = m_test + c_test

    train_data, val_data, test_data = deduplicate_and_prevent_leakage(raw_train, raw_val, raw_test)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_DIR / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    with open(PROCESSED_DIR / "val.json", "w", encoding="utf-8") as f:
        json.dump(val_data, f, ensure_ascii=False, indent=2)
    with open(PROCESSED_DIR / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    # Step 4: Summary Statistics
    print("\n[4/4] Computing dataset statistics...")
    all_data = train_data + val_data + test_data
    intents_counter = Counter(r["intent"] for r in all_data)
    langs_counter = Counter(r["lang"] for r in all_data)

    summary = {
        "dataset_name": "Amazon MASSIVE + Vaani AI Curated Multilingual NLU",
        "license": "CC-BY-4.0 (MASSIVE) + Proprietary Curated Extensions",
        "split_counts": {
            "train": len(train_data),
            "validation": len(val_data),
            "test": len(test_data),
            "total": len(all_data),
        },
        "intent_distribution": dict(intents_counter.most_common()),
        "language_distribution": dict(langs_counter.most_common()),
        "mapped_intents_count": len(intents_counter),
    }

    with open(PROCESSED_DIR / "dataset_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("DATASET PREPARATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Total Utterances : {len(all_data)}")
    print(f"  - Train Split  : {len(train_data)} ({len(train_data)/len(all_data)*100:.1f}%)")
    print(f"  - Val Split    : {len(val_data)} ({len(val_data)/len(all_data)*100:.1f}%)")
    print(f"  - Test Split   : {len(test_data)} ({len(test_data)/len(all_data)*100:.1f}%)")
    print(f"Total Unique Intents : {len(intents_counter)}")
    print("\nIntent Distribution:")
    for intent, cnt in intents_counter.most_common():
        print(f"  - {intent:20s}: {cnt:5d}")
    print("\nLanguage Distribution:")
    for lang, cnt in langs_counter.most_common():
        print(f"  - {lang:20s}: {cnt:5d}")
    print("=" * 60)


if __name__ == "__main__":
    main()
