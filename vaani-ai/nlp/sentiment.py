"""Language-aware multilingual sentiment analysis for Vaani AI.

Supports 20 languages:
- Core: English (en), Hindi (hi), Marathi (mr), Gujarati (gu), Bengali (bn), Tamil (ta), Hinglish (hinglish).
- Extended: Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), Dutch (nl),
            Russian (ru), Arabic (ar), Japanese (ja), Chinese (zh), Korean (ko), Telugu (te), Urdu (ur).

Features:
- Native VADER integration for English.
- Localized language-aware sentiment lexicons with valence scoring.
- Comprehensive negation scope detection (reversing sentiment polarity).
- Multi-lingual intensifier handling (boosting sentiment strength).
- Cross-lingual emoji sentiment scoring (positive/negative emoji valence).
- Completely independent of external LLMs or network connectivity.
- Returns label (positive/negative/neutral), compound score, confidence, scores breakdown, and method badge.
"""

import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .preprocess import tokenize
from .languages import LANGUAGES, HINGLISH

_vader = SentimentIntensityAnalyzer()

# ----------------- 1. Universal Emoji Valence -----------------
EMOJI_VALENCE = {
    # Strong positive (+0.6)
    "😀": 0.6, "😃": 0.6, "😄": 0.6, "😁": 0.6, "😊": 0.5, "🥰": 0.8,
    "😍": 0.8, "🤩": 0.7, "😘": 0.6, "👍": 0.5, "❤️": 0.8, "💖": 0.8,
    "🎉": 0.6, "✨": 0.5, "👏": 0.6, "🙌": 0.6, "🔥": 0.6, "💯": 0.7,
    # Strong negative (-0.6)
    "😞": -0.6, "😔": -0.6, "😟": -0.6, "😕": -0.5, "🙁": -0.5, "☹️": -0.6,
    "😣": -0.6, "😖": -0.7, "😫": -0.7, "😩": -0.7, "🥺": -0.4, "😢": -0.7,
    "😭": -0.8, "😤": -0.6, "😠": -0.7, "😡": -0.8, "🤬": -0.9, "👎": -0.6,
    "💔": -0.8, "😿": -0.6, "🤢": -0.7, "🤮": -0.8,
}

# ----------------- 2. Language-Aware Negation Words -----------------
NEGATIONS = {
    "en": {"not", "no", "never", "hardly", "scarcely", "barely", "without", "neither", "nor", "dont", "isnt", "arent", "wasnt", "werent", "wont"},
    "hi": {"नहीं", "न", "मत", "ना", "बिना"},
    "mr": {"नाही", "नाहीत", "नका", "नको", "नव्हते", "नसेल", "न", "विना"},
    "gu": {"નથી", "નહીં", "ના", "ન", "વિના"},
    "hinglish": {"nahi", "nahin", "na", "mat", "nhi", "nhn", "bina"},
    "bn": {"না", "নয়", "নেই", "নহে", "বিনা"},
    "ta": {"இல்லை", "அல்ல", "கூடாது", "வேண்டாம்"},
    "te": {"లేదు", "కాదు", "వద్దు"},
    "ur": {"نہیں", "نہ", "مت", "بغیر"},
    "es": {"no", "nunca", "jamás", "ni", "sin"},
    "fr": {"pas", "non", "ne", "jamais", "plus", "sans"},
    "de": {"nicht", "kein", "keine", "nie", "niemals", "ohne"},
    "it": {"non", "mai", "nessun", "nessuno", "senza"},
    "pt": {"não", "nao", "nunca", "jamais", "nem", "sem"},
    "nl": {"niet", "geen", "nooit", "zonder"},
    "ru": {"не", "нет", "никогда", "без"},
    "ar": {"لا", "لم", "لن", "ليس", "ما", "غير", "بدون"},
    "ja": {"ない", "ません", "ず", "なく"},
    "zh": {"不", "没", "没有", "无", "别"},
    "ko": {"안", "못", "아닌", "않다", "없다"},
}

# ----------------- 3. Language-Aware Intensifiers -----------------
INTENSIFIERS = {
    "en": {"very", "extremely", "really", "so", "super", "absolutely", "highly", "too"},
    "hi": {"बहुत", "काफी", "ज़्यादा", "ज्यादा", "अत्यधिक", "खूब", "बेहद", "बिल्कुल", "एकदम"},
    "mr": {"खूप", "फार", "अतिशय", "फारच", "प्रचंड", "मुळीच", "अगदी", "नक्कीच"},
    "gu": {"ખૂબ", "ઘણું", "અતિશય", "ભારે", "બિલકુલ", "સાવ"},
    "hinglish": {"bahut", "bohot", "kafi", "jyada", "zyada", "super", "boht", "bhot", "bilkul", "ekdam"},
    "bn": {"খুব", "অনেক", "অত্যন্ত", "দারুণ", "একদম", "মোটেই"},
    "ta": {"மிகவும்", "ரொம்ப", "அதிகமாக", "ரொம்பவே"},
    "te": {"చాలా", "ఎక్కువ", "మరీ"},
    "ur": {"بہت", "زیادہ", "بےحد", "بالکل"},
    "es": {"muy", "mucho", "extremadamente", "tan", "super"},
    "fr": {"très", "tres", "vraiment", "beaucoup", "extrêmement", "trop"},
    "de": {"sehr", "wirklich", "extrem", "besonders", "total"},
    "it": {"molto", "davvero", "estremamente", "troppo", "assolutamente"},
    "pt": {"muito", "demais", "extremamente", "realmente", "super"},
    "nl": {"heel", "erg", "zeer", "echt", "ontzettend"},
    "ru": {"очень", "крайне", "действительно", "совсем", "слишком"},
    "ar": {"جدا", "كثيرا", "للغاية", "جداً"},
    "ja": {"とても", "すごく", "大変", "非常に", "本当に"},
    "zh": {"很", "非常", "特别", "太", "极"},
    "ko": {"매우", "너무", "정말", "아주", "진짜"},
}

# ----------------- 4. Language-Aware Sentiment Lexicons -----------------
# Scores: Positive (+1.0), Negative (-1.0)
LEXICON_POS = {
    "hi": {"अच्छा", "अच्छी", "अच्छे", "बढ़िया", "शानदार", "खुश", "प्रसन्न", "प्यार", "धन्यवाद", "शुक्रिया", "सुंदर", "मज़ा", "मजेदार", "उत्तम", "बेहतरीन", "आभार", "सराहनीय", "रोमांचक", "संतुष्ट", "सुखद", "मस्त"},
    "mr": {"छान", "सुंदर", "मस्त", "आनंद", "आनंदी", "खुश", "भारी", "उत्तम", "धन्यवाद", "आभार", "कौतुक", "गोड", "प्रसन्न", "आवडले", "मजा", "सुख", "सुंदर"},
    "gu": {"સરસ", "સારું", "સારી", "સારો", "આનંદ", "ખુશ", "મજા", "ધન્યવાદ", "આભાર", "ઉત્તમ", "સુંદર", "જોરદાર", "પ્રસન્ન", "પ્રેમ", "ગમ્યું", "સુખી"},
    "hinglish": {"acha", "accha", "badhiya", "badiya", "mast", "khush", "pyaar", "pyar", "shukriya", "dhanyavad", "zabardast", "shandar", "smart", "super", "sundar", "badiyaa", "awesome", "great", "best"},
    "bn": {"ভালো", "সুন্দর", "চমৎকার", "आनন্দ", "আনন্দ", "খুশি", "ধন্যবাদ", "ভালোবাসা", "সেরা", "উত্তম", "উপকারী", "সুখী"},
    "ta": {"நல்ல", "அழகு", "மகிழ்ச்சி", "சந்தோஷம்", "நன்றி", "அருமை", "சிறப்பு", "அன்பு", "இனிமை", "உயர்வு"},
    "te": {"మంచి", "బాగుంది", "సంతోషం", "ఆనందం", "ధన్యవాదాలు", "అద్భుతం", "చక్కగా", "ప్రేమ", "ఉత్తమ"},
    "ur": {"اچھا", "اچھی", "بہترین", "خوش", "محبت", "شکریہ", "شاندار", "عمدہ", "خوبصورت", "پسند"},
    "es": {"bueno", "buena", "excelente", "feliz", "gracias", "genial", "amor", "maravilloso", "perfecto", "alegría", "bien", "gusto"},
    "fr": {"bon", "bonne", "bien", "super", "heureux", "heureuse", "merci", "génial", "excellent", "amour", "joie", "magnifique"},
    "de": {"gut", "toll", "super", "glücklich", "danke", "fantastisch", "wunderbar", "liebe", "schön", "perfekt", "freude"},
    "it": {"buono", "buona", "ottimo", "felice", "grazie", "bello", "bellissimo", "amore", "fantastico", "meraviglioso", "piacere", "bene"},
    "pt": {"bom", "boa", "ótimo", "otimo", "feliz", "obrigado", "obrigada", "lindo", "amor", "maravilhoso", "excelente", "alegria", "bem"},
    "nl": {"goed", "geweldig", "blij", "dank", "fijn", "mooi", "liefde", "uitstekend", "prachtig", "leuk"},
    "ru": {"хорошо", "хороший", "отлично", "счастливый", "спасибо", "прекрасно", "любовь", "радость", "замечательно", "красивый"},
    "ar": {"جيد", "جميل", "رائع", "سعيد", "شكرا", "ممتاز", "حب", "فرح", "عظيم", "أفضل"},
    "ja": {"良い", "素晴らしい", "嬉しい", "幸せ", "ありがとう", "最高", "好き", "楽しい", "美しい", "愛"},
    "zh": {"好", "棒", "优秀", "高兴", "开心", "快乐", "谢谢", "喜欢", "爱", "完美", "太棒了", "精彩"},
    "ko": {"좋은", "좋다", "훌륭한", "훌륭", "행복", "감사", "기쁨", "사랑", "최고", "멋진", "즐거운"},
}

LEXICON_NEG = {
    "hi": {"बुरा", "बुरी", "बुरे", "खराब", "उदास", "गुस्सा", "दुखी", "दुख", "बेकार", "नफरत", "परेशान", "कष्ट", "तनाव", "दर्द", "निराश", "घटिया", "घिनौना", "अप्रिय", "रोना", "रो"},
    "mr": {"वाईट", "खराब", "उदास", "दुःख", "दुःखी", "राग", "नाराज", "निराश", "त्रास", "कंटाळा", "तणाव", "रडू", "घाणेरडे", "चूक", "वेदना"},
    "gu": {"ખરાબ", "ઉદાસ", "દુઃખ", "દુઃખી", "ગુસ્સો", "નફરત", "હેરાન", "નિરાશ", "કંટાળો", "રડવું", "બેકાર", "ચિંતા", "પીડા", "તકલીફ"},
    "hinglish": {"bura", "kharab", "udaas", "udas", "dukhi", "gussa", "bekar", "nafrat", "pareshan", "preshan", "ghatiya", "chinta", "rona", "sad", "bekaar", "worst"},
    "bn": {"খারাপ", "মন্দ", "দুঃখ", "দুঃখী", "রাগ", "ঘৃণা", "বিরক্ত", "হতাশ", "কষ্ট", "ভয়ানক", "বেদনা"},
    "ta": {"மோசமான", "கெட்ட", "வருத்தம்", "துன்பம்", "கோபம்", "வெறுப்பு", "சோகம்", "வலி", "கவலை", "அவலம்"},
    "te": {"చెడు", "చెడ్డ", "బాధ", "దుఃఖం", "కోపం", "అసంతృప్తి", "భయం", "విచారం"},
    "ur": {"برا", "بری", "خراب", "اداس", "غصہ", "دکھی", "نفرت", "پریشان", "تکلیف", "درد"},
    "es": {"malo", "mala", "terrible", "triste", "odio", "horrible", "peor", "enfado", "pena", "asco", "dolor"},
    "fr": {"mauvais", "mauvaise", "mal", "triste", "horrible", "nul", "haine", "colère", "pire", "douleur", "peur"},
    "de": {"schlecht", "traurig", "schrecklich", "furchtbar", "hass", "wut", "schlimm", "böse", "eklig", "angst"},
    "it": {"cattivo", "male", "terribile", "triste", "odio", "orribile", "peggiore", "rabbia", "dolore", "brutto"},
    "pt": {"mau", "má", "ruim", "terrível", "terrivel", "triste", "ódio", "odio", "horrível", "horrivel", "pior", "raiva", "dor"},
    "nl": {"slecht", "vreselijk", "verdrietig", "haat", "boos", "erg", "pijn", "angst", "stom"},
    "ru": {"плохо", "плохой", "ужасно", "грустно", "ненависть", "злость", "страшно", "боль", "печаль", "отвратительно"},
    "ar": {"سيء", "قبيح", "حزين", "غاضب", "كره", "فظيع", "ألم", "خوف", "فاشل", "شر"},
    "ja": {"悪い", "酷い", "酷く", "酷", "悲しい", "怒り", "嫌い", "嫌", "苦しい", "辛い", "最悪", "怖"},
    "zh": {"坏", "差", "糟糕", "难过", "伤心", "生气", "讨厌", "恨", "可怕", "痛苦", "失败"},
    "ko": {"나쁜", "나쁘다", "끔찍한", "끔찍", "슬픈", "슬프다", "슬프", "화남", "싫다", "미움", "고통", "최악"},
}


def _label(compound: float) -> str:
    """Standardized compound polarity threshold."""
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def _extract_emoji_score(text: str) -> float:
    """Extract cumulative emoji sentiment score."""
    score = 0.0
    for ch, val in EMOJI_VALENCE.items():
        if ch in text:
            score += val * text.count(ch)
    return score


def _scan_cjk_sentiment(text: str, pos_set: set[str], neg_set: set[str], negation_words: set[str], intensifier_words: set[str]) -> tuple[float, int, int]:
    """Character/substring scanning for non-space-delimited or agglutinative languages (zh, ja, ko)."""
    norm = text.lower()
    all_terms = [(term, "pos") for term in sorted(pos_set, key=len, reverse=True)] + \
                [(term, "neg") for term in sorted(neg_set, key=len, reverse=True)]

    occupied = [False] * len(norm)
    events = []

    for term, polarity in all_terms:
        if not term:
            continue
        start = 0
        while True:
            idx = norm.find(term, start)
            if idx == -1:
                break
            end = idx + len(term)
            if not any(occupied[idx:end]):
                for k in range(idx, end):
                    occupied[k] = True
                events.append((idx, end, term, polarity))
            start = idx + 1

    events.sort(key=lambda x: x[0])

    valence_sum = 0.0
    pos_count = 0
    neg_count = 0

    for idx, end, term, polarity in events:
        # Check context window (up to 5 chars before and 5 chars after)
        ctx_before = norm[max(0, idx - 5): idx]
        ctx_after = norm[end: min(len(norm), end + 5)]

        is_negated = any(nw in ctx_before or nw in ctx_after for nw in negation_words if nw)
        is_intensified = any(iw in ctx_before or iw in ctx_after for iw in intensifier_words if iw)
        mult = 1.5 if is_intensified else 1.0

        if polarity == "pos":
            score = 1.0 * mult
            if is_negated:
                score = -score * 0.9
                neg_count += 1
            else:
                pos_count += 1
            valence_sum += score
        else:
            score = -1.0 * mult
            if is_negated:
                score = 0.8 * mult
                pos_count += 1
            else:
                neg_count += 1
            valence_sum += score

    return valence_sum, pos_count, neg_count


def analyze_multilingual_rules(text: str, lang: str) -> dict:
    """Language-aware sentiment scoring with bidirectional negation and intensifier windows."""
    pos_set = set(LEXICON_POS.get(lang, set()))
    neg_set = set(LEXICON_NEG.get(lang, set()))
    negation_words = set(NEGATIONS.get(lang, set()))
    intensifier_words = set(INTENSIFIERS.get(lang, set()))

    # Include Hinglish fallbacks if language is Hinglish or Hindi
    if lang in ("hinglish", "hi"):
        pos_set = pos_set.union(LEXICON_POS["hinglish"])
        neg_set = neg_set.union(LEXICON_NEG["hinglish"])
        negation_words = negation_words.union(NEGATIONS["hinglish"])
        intensifier_words = intensifier_words.union(INTENSIFIERS["hinglish"])

    if lang in ("zh", "ja", "ko"):
        valence_sum, pos_count, neg_count = _scan_cjk_sentiment(text, pos_set, neg_set, negation_words, intensifier_words)
        neu_count = 0 if (pos_count + neg_count > 0) else 1
    else:
        tokens = tokenize(text)
        valence_sum = 0.0
        pos_count = 0
        neg_count = 0
        neu_count = 0

        # Bidirectional window-based token analysis
        n = len(tokens)
        for i, t in enumerate(tokens):
            # Look behind (preceding 2 tokens) AND look ahead (succeeding 2 tokens)
            # This handles SVO (English, European) and SOV (Hindi, Marathi, Gujarati, etc.) syntax
            prev_window = tokens[max(0, i - 2): i]
            next_window = tokens[i + 1: min(n, i + 3)]

            is_negated = any(p in negation_words for p in prev_window) or any(p in negation_words for p in next_window)
            is_intensified = any(p in intensifier_words for p in prev_window) or any(p in intensifier_words for p in next_window)
            mult = 1.5 if is_intensified else 1.0

            if t in pos_set:
                score = 1.0 * mult
                if is_negated:
                    score = -score * 0.9  # negated positive becomes moderately negative
                    neg_count += 1
                else:
                    pos_count += 1
                valence_sum += score
            elif t in neg_set:
                score = -1.0 * mult
                if is_negated:
                    score = 0.8 * mult   # negated negative becomes mildly positive
                    pos_count += 1
                else:
                    neg_count += 1
                valence_sum += score
            else:
                neu_count += 1

    # Emoji fusion
    emoji_score = _extract_emoji_score(text)
    total_valence = valence_sum + emoji_score

    # Normalization into [-1.0, 1.0]
    total_sentiment_events = pos_count + neg_count + (1 if emoji_score != 0 else 0)
    if total_sentiment_events > 0:
        compound = round(total_valence / max(1.0, total_sentiment_events + 0.5), 3)
        compound = max(-1.0, min(1.0, compound))
        confidence = round(min(0.98, max(0.75, 0.65 + abs(compound) * 0.35)), 3)
    else:
        compound = 0.0
        confidence = 0.85  # high confidence that text is factual / neutral

    # Calculate balanced component proportions (pos, neu, neg) summing to 1.0 (100%)
    pos_weight = float(pos_count) + (1.0 if emoji_score > 0 else 0.0)
    neg_weight = float(neg_count) + (1.0 if emoji_score < 0 else 0.0)
    neu_weight = float(neu_count)

    total_weight = pos_weight + neg_weight + neu_weight
    if total_weight > 0:
        pos_frac = round(pos_weight / total_weight, 3)
        neg_frac = round(neg_weight / total_weight, 3)
        neu_frac = round(max(0.0, 1.0 - (pos_frac + neg_frac)), 3)
    else:
        pos_frac, neg_frac, neu_frac = 0.0, 0.0, 1.0

    import math
    if math.isnan(pos_frac) or math.isinf(pos_frac): pos_frac = 0.0
    if math.isnan(neg_frac) or math.isinf(neg_frac): neg_frac = 0.0
    if math.isnan(neu_frac) or math.isinf(neu_frac): neu_frac = 1.0
    if math.isnan(compound) or math.isinf(compound): compound = 0.0
    if math.isnan(confidence) or math.isinf(confidence): confidence = 0.85

    tier = LANGUAGES.get(lang, {}).get("tier", "core")
    method_name = f"multilingual lexicon ({tier})"

    return {
        "label": _label(compound),
        "compound": float(compound),
        "confidence": float(confidence),
        "pos": pos_frac,
        "neu": neu_frac,
        "neg": neg_frac,
        "scores": {
            "pos": pos_frac,
            "neg": neg_frac,
            "neu": neu_frac,
            "emoji": round(emoji_score, 2),
            "pos_count": pos_count,
            "neg_count": neg_count,
            "neu_count": neu_count,
        },
        "method": method_name,
        "support_tier": tier,
    }


def analyze(text: str, lang: str = "en") -> dict:
    """Primary sentiment analyzer API used by pipeline and endpoints.

    - English: VADER with Emoji fusion and calibrated confidence.
    - Other languages: Multilingual Rule-Based Valence Engine (Offline, local, instant).
    """
    import math
    text = (text or "").strip()
    if not text:
        return {
            "label": "neutral",
            "compound": 0.0,
            "confidence": 0.0,
            "pos": 0.0,
            "neu": 1.0,
            "neg": 0.0,
            "scores": {"pos": 0.0, "neu": 1.0, "neg": 0.0, "emoji": 0.0},
            "method": "empty",
            "support_tier": "core",
        }

    # For English: VADER
    if lang == "en":
        s = _vader.polarity_scores(text)
        emoji_score = _extract_emoji_score(text)
        compound = s["compound"]
        # Blend emoji if present
        if emoji_score != 0:
            compound = round(max(-1.0, min(1.0, compound * 0.7 + (emoji_score * 0.3))), 3)

        compound = max(-1.0, min(1.0, compound))
        confidence = round(min(0.99, max(0.70, 0.60 + abs(compound) * 0.40)), 3) if abs(compound) >= 0.05 else 0.85

        pos_frac = float(s.get("pos", 0.0))
        neu_frac = float(s.get("neu", 1.0))
        neg_frac = float(s.get("neg", 0.0))

        tot = pos_frac + neu_frac + neg_frac
        if tot > 0:
            pos_frac = round(pos_frac / tot, 3)
            neg_frac = round(neg_frac / tot, 3)
            neu_frac = round(max(0.0, 1.0 - (pos_frac + neg_frac)), 3)
        else:
            pos_frac, neu_frac, neg_frac = 0.0, 1.0, 0.0

        if math.isnan(pos_frac) or math.isinf(pos_frac): pos_frac = 0.0
        if math.isnan(neu_frac) or math.isinf(neu_frac): neu_frac = 1.0
        if math.isnan(neg_frac) or math.isinf(neg_frac): neg_frac = 0.0
        if math.isnan(compound) or math.isinf(compound): compound = 0.0

        return {
            "label": _label(compound),
            "compound": float(compound),
            "confidence": float(confidence),
            "pos": pos_frac,
            "neu": neu_frac,
            "neg": neg_frac,
            "scores": {"pos": pos_frac, "neu": neu_frac, "neg": neg_frac, "emoji": round(emoji_score, 2)},
            "method": "VADER (English)",
            "support_tier": "core",
        }

    # For all other languages: Multilingual rule-based valence engine
    return analyze_multilingual_rules(text, lang)
