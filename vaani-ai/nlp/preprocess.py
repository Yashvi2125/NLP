"""Advanced multilingual text preprocessing for Vaani AI.

Supports:
- Unicode normalization (NFKC, zero-width stripping, combining mark preservation for Devanagari, Gujarati, Bengali, Tamil).
- Indic and Latin punctuation handling (Danda '।', Double Danda '॥', quotation marks, dashes).
- Comprehensive stopword sets for English, Hindi, Marathi, Gujarati, Hinglish, Bengali, Tamil.
- Safe Hinglish normalization without altering English words or named entities.
- Mixed-script and code-switching detection.
- Language-aware stemming (English suffix stripping, preserving Indic inflections to protect semantic intent).
- Preserves original input text throughout all stages.
"""

import re
import unicodedata

# ----------------- Contractions -----------------
CONTRACTIONS = {
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "i'd": "i would",
    "you're": "you are",
    "you've": "you have",
    "you'll": "you will",
    "you'd": "you would",
    "he's": "he is",
    "he'll": "he will",
    "he'd": "he would",
    "she's": "she is",
    "she'll": "she will",
    "she'd": "she would",
    "it's": "it is",
    "it'll": "it will",
    "it'd": "it would",
    "we're": "we are",
    "we've": "we have",
    "we'll": "we will",
    "we'd": "we would",
    "they're": "they are",
    "they've": "they have",
    "they'll": "they will",
    "they'd": "they would",
    "that's": "that is",
    "that'll": "that will",
    "that'd": "that would",
    "who's": "who is",
    "who'll": "who will",
    "who'd": "who would",
    "what's": "what is",
    "what're": "what are",
    "what'll": "what will",
    "what'd": "what would",
    "where's": "where is",
    "where'll": "where will",
    "where'd": "where would",
    "when's": "when is",
    "why's": "why is",
    "how's": "how is",
    "there's": "there is",
    "here's": "here is",
    "can't": "cannot",
    "cannot": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "mustn't": "must not",
    "let's": "let us",
    "ain't": "is not",
}

# ----------------- Stopwords -----------------
# Carefully curated function words; critical intent keywords (time, date, weather, music, alarm, joke)
# are explicitly EXCLUDED to preserve strong intent signals.
STOPWORDS = {
    "en": {
        "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "being",
        "to", "of", "in", "on", "at", "for", "and", "or", "but", "if", "so", "it",
        "this", "that", "these", "those", "i", "you", "he", "she", "we", "they",
        "me", "him", "her", "us", "them", "my", "your", "his", "their", "our",
        "with", "as", "by", "from", "do", "does", "did", "have", "has", "had",
        "having", "can", "could", "would", "should", "will", "shall", "just",
    },
    "hi": {
        "है", "हैं", "था", "थे", "थी", "का", "की", "के", "को", "में", "से", "पर",
        "और", "या", "यह", "वह", "मैं", "तुम", "आप", "हम", "वे", "एक", "भी", "तो",
        "ही", "कर", "ने", "हो", "हूँ", "हुए", "कि", "जो", "करके", "दिया", "लिए",
        "तक", "था", "रहे", "रहा", "रही", "सकते", "सकता", "सकती", "वाले", "वाला",
    },
    "mr": {
        "आहे", "आहेत", "होते", "होती", "होता", "आणि", "किंवा", "हा", "ही", "हे",
        "तो", "ती", "ते", "मी", "तू", "तुम्ही", "मला", "तुला", "त्यांना", "त्याला",
        "का", "काय", "या", "त्या", "मध्ये", "वर", "ने", "नी", "चे", "ची", "चा",
        "च्या", "साठी", "पण", "नाही", "होऊन", "असेल", "झाले", "झाली", "केले", "केली",
    },
    "gu": {
        "છે", "છું", "છો", "હતા", "હતી", "હતો", "અને", "કે", "આ", "તે", "હું",
        "તું", "તમે", "મને", "તને", "તેને", "અમને", "શું", "ના", "માં", "થી", "નો",
        "ની", "નું", "ને", "પણ", "માટે", "નથી", "ન", "તો", "જ", "એ", "થઈ", "કરી",
    },
    "hinglish": {
        "hai", "hain", "tha", "the", "thi", "ka", "ki", "ke", "ko", "mein", "se",
        "par", "aur", "ya", "yeh", "woh", "main", "tum", "aap", "hum", "ek",
        "bhi", "toh", "to", "hi", "kar", "ne", "ho", "hoon", "hu", "karke", "diya",
        "liye", "तक", "raha", "rahe", "rahi", "sakte", "sakta", "sakti", "wala",
        "wali", "vale", "mera", "meri", "mere", "tera", "teri", "tere", "apna",
        "apne", "apni", "kuch", "sab", "yeh", "wo",
    },
    "bn": {
        "হয়", "আছে", "ছিল", "এবং", "বা", "এই", "সেই", "আমি", "তুমি", "আপনি",
        "আমরা", "আমাকে", "তোমাকে", "তার", "কী", "কেন", "তে", "থেকে", "এর", "ও",
        "হলো", "করে", "জন্য", "না", "কি", "হতে", "যায়", "একটি",
    },
    "ta": {
        "இருக்கிறது", "இருந்தது", "மற்றும்", "அல்லது", "இந்த", "அந்த", "நான்",
        "நீ", "நீங்கள்", "நாம்", "எனக்கு", "உனக்கு", "அவருக்கு", "என்ன", "ஏன்",
        "இல்", "இருந்து", "உடைய", "ஒரு", "செய்து", "இல்லை", "ஆகும்",
    },
    "es": {"el", "la", "los", "las", "un", "una", "de", "del", "en", "y", "o", "que", "es", "son", "por", "para", "con"},
    "fr": {"le", "la", "les", "un", "une", "des", "de", "du", "en", "et", "ou", "que", "est", "sont", "pour", "avec", "dans"},
    "de": {"der", "die", "das", "ein", "eine", "und", "oder", "ist", "sind", "zu", "von", "mit", "in", "auf", "für"},
    "it": {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "da", "in", "con", "su", "per", "tra", "fra", "è", "sono", "e", "o", "che"},
    "pt": {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "em", "para", "com", "por", "é", "são", "e", "ou", "que", "não", "no", "na"},
    "nl": {"de", "het", "een", "van", "in", "op", "te", "met", "voor", "is", "zijn", "en", "of", "niet", "naar", "om", "dat", "die"},
    "ru": {"и", "в", "не", "на", "я", "что", "с", "он", "а", "по", "это", "она", "этот", "к", "но", "они", "мы", "как", "из", "у", "то"},
    "ar": {"في", "من", "على", "إلى", "أن", "هذا", "هذه", "التي", "الذي", "مع", "عن", "لا", "ما", "كان", "هو", "هي", "أو", "و"},
    "ja": {"の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある", "いる", "も", "する", "から", "な", "こと", "として"},
    "zh": {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你"},
    "ko": {"이", "그", "저", "것", "수", "등", "들", "및", "에서", "으로", "로", "에게", "와", "과", "도", "은", "는", "이", "가", "을", "를"},
    "te": {"మరియు", "కూడా", "లేదా", "ఈ", "ఆ", "నేను", "నువ్వు", "మీరు", "మేము", "నాకు", "ఎందుకు", "ఏమిటి", "ఉంది", "ఉన్నాయి", "లో", "నుండి"},
    "ur": {"ہے", "ہیں", "تھا", "تھے", "تھی", "کا", "کی", "کے", "کو", "میں", "سے", "پر", "اور", "یا", "یہ", "وہ", "میں", "آپ", "ہم", "ایک"},
}

# Protected English words that must NEVER be normalized as Hinglish
PROTECTED_ENGLISH = {
    "the", "to", "me", "so", "is", "in", "it", "at", "on", "he", "she", "we", "be",
    "do", "go", "no", "up", "my", "by", "or", "an", "as", "if", "for", "and", "not",
    "but", "all", "any", "can", "had", "has", "her", "him", "his", "how", "man",
    "new", "now", "old", "our", "out", "see", "two", "way", "who", "boy", "did",
    "its", "let", "put", "say", "too", "use", "time", "date", "weather", "music",
    "play", "alarm", "help", "joke", "call", "name", "show", "tell", "news", "stop",
    "open", "turn", "good", "nice", "fine", "what", "when", "where", "which", "will",
    "with", "would", "about", "there", "their", "today", "tomorrow", "yesterday",
    "please", "thanks", "thank", "you", "love", "sad", "happy", "great", "day",
    "set", "check", "current", "morning", "night", "afternoon", "evening",
}

# Protected proper names (common Indian and international names)
PROTECTED_NAMES = {
    "rahul", "priya", "amit", "yashvi", "vikram", "ananya", "rohit", "pooja",
    "deepak", "rohan", "sachin", "aniket", "neha", "dinesh", "kalpesh", "sunil",
    "aarav", "delhi", "mumbai", "pune", "bangalore", "kolkata", "chennai",
    "ahmedabad", "jaipur", "surat", "nagpur", "london", "paris", "tokyo",
}

# Canonical Roman Hindi mappings for common phonetic variants
HINGLISH_CANONICAL = {
    # Greetings & Politeness
    "namastey": "namaste", "namaskar": "namaste", "nmste": "namaste",
    "shukriya": "shukriya", "sukriya": "shukriya", "sukria": "shukriya", "shukria": "shukriya",
    "dhanyawad": "dhanyavad", "dhanyawaad": "dhanyavad", "dhanyavada": "dhanyavad", "dhanybaad": "dhanyavad",
    "alwida": "alvida",
    # Adjectives / Emotion
    "bohot": "bahut", "boht": "bahut", "bhot": "bahut", "bahoot": "bahut",
    "thik": "theek", "teek": "theek", "theeq": "theek",
    "acha": "accha", "achha": "accha", "achaa": "accha",
    "badiya": "badhiya", "badeya": "badhiya", "badia": "badhiya",
    "khus": "khush", "udaas": "udaas", "udas": "udaas",
    "preshan": "pareshan", "pareshaan": "pareshan",
    # Interrogatives & Core Verbs
    "kyaa": "kya", "kya": "kya",
    "kaise": "kaise", "kese": "kaise", "kaisa": "kaise", "kaisi": "kaise",
    "kyun": "kyun", "kyu": "kyun", "kyoo": "kyun",
    "kahan": "kahan", "kaha": "kahan", "kahn": "kahan",
    "batao": "batao", "btao": "batao", "bataao": "batao", "batado": "batao", "bataye": "batao",
    "karo": "karo", "kro": "karo", "kar do": "karo", "kardo": "karo",
    "karna": "karna", "krna": "karna",
    "baja": "bajao", "bajado": "bajao", "bjao": "bajao",
    "chalao": "chalao", "chlao": "chalao", "chalado": "chalao",
    # Pronouns & Auxiliaries
    "mjhe": "mujhe", "muze": "mujhe",
    "tmhara": "tumhara", "tumhra": "tumhara",
    "apka": "aapka",
    "ktna": "kitna", "ktne": "kitne",
    "smay": "samay",
    "tarikh": "tareekh", "tareeq": "tareekh",
    "chlo": "chalo",
    "subha": "subah",
    "mosam": "mausam",
    "chahiye": "chahiye", "chiye": "chahiye", "chahie": "chahiye",
    "rha": "raha", "rhe": "rahe", "rhi": "rahi",
    "hta": "hota", "hti": "hoti", "hte": "hote",
    "bhayi": "bhai", "bhiya": "bhai",
    "yrr": "yaar", "yaarr": "yaar",
    "nhi": "nahin", "nhn": "nahin", "nahi": "nahin",
    "haa": "haan", "han": "haan",
    "gaana": "gaana", "gana": "gaana", "gaane": "gaana", "gane": "gaana",
}

# Suffixes for English-only suffix stemmer
_EN_SUFFIXES = ("ingly", "edly", "ing", "ed", "ly", "es", "s")


def expand_contractions(text: str) -> str:
    """Expand standard English contractions generally using comprehensive dictionary."""
    if not text:
        return ""
    t = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    for contr, repl in CONTRACTIONS.items():
        pattern = r"\b" + re.escape(contr) + r"\b"
        t = re.sub(pattern, repl, t, flags=re.IGNORECASE)
    return t


def _is_indic_char(ch: str) -> bool:
    """Check if character belongs to Devanagari, Gujarati, Bengali, Tamil, Telugu, or Urdu/Arabic scripts."""
    cp = ord(ch)
    return (
        (0x0900 <= cp <= 0x097F)  # Devanagari (Hindi, Marathi, Sanskrit)
        or (0x0A80 <= cp <= 0x0AFF)  # Gujarati
        or (0x0980 <= cp <= 0x09FF)  # Bengali
        or (0x0B80 <= cp <= 0x0BFF)  # Tamil
        or (0x0C00 <= cp <= 0x0C7F)  # Telugu
        or (0x0600 <= cp <= 0x06FF)  # Arabic / Urdu
        or (0x0750 <= cp <= 0x077F)  # Arabic Supplement (Urdu)
        or (0x0964 <= cp <= 0x0965)  # Indic Dandas (। ॥)
    )


def _keep_char(ch: str) -> bool:
    """Keep letters, combining marks (matras, virama, nukta), numbers, whitespace, and punctuation."""
    cat = unicodedata.category(ch)
    return (
        cat[0] in "LMN"
        or ch.isspace()
        or ch in "'?!.,:@-।॥\"()[]"
        or _is_indic_char(ch)
    )


def normalize_unicode(text: str) -> str:
    """Normalize Unicode (NFKC) while stripping invisible zero-width characters."""
    if not text:
        return ""
    # Strip zero-width spaces/joiners often emitted by mobile IMEs if unattached
    text = re.sub(r"[\u200B\uFEFF]", "", text)
    # NFKC normalizes composed/decomposed marks canonicalizing nuktas and ligatures
    text = unicodedata.normalize("NFKC", text)
    # Replace URLs
    text = re.sub(r"https?://\S+", " ", text)
    # Replace Danda with space for token separation while preserving rhythm
    text = text.replace("॥", " ").replace("।", " ")
    # Filter non-printable / emoji noise while preserving all combining marks
    text = "".join(ch if _keep_char(ch) else " " for ch in text)
    # Collapse multiple whitespaces
    return re.sub(r"\s+", " ", text).strip()


def normalize(text: str) -> str:
    """Primary text normalizer: returns clean normalized string copy (does NOT mutate original)."""
    return normalize_unicode(text)


def normalize_hinglish_token(token: str) -> str:
    """Normalize a single Roman Hindi token safely, guarding English words and proper names."""
    low = token.lower()
    if low in PROTECTED_ENGLISH or low in PROTECTED_NAMES:
        return token

    # Collapse character elongation (e.g., 'booohoooot' -> 'bohot')
    collapsed = re.sub(r"(.)\1{2,}", r"\1", low)
    if collapsed in HINGLISH_CANONICAL:
        return HINGLISH_CANONICAL[collapsed]
    if low in HINGLISH_CANONICAL:
        return HINGLISH_CANONICAL[low]
    return collapsed


def normalize_hinglish_text(text: str) -> str:
    """Normalize full Hinglish sentence with protection for English keywords."""
    tokens = re.findall(r"[^\s?!.,:@-]+|[?!.,:@-]", text)
    out = []
    for t in tokens:
        if re.match(r"^[a-zA-Z]+$", t):
            out.append(normalize_hinglish_token(t))
        else:
            out.append(t)
    # Reassemble spacing cleanly around punctuation
    res = " ".join(out)
    return re.sub(r"\s+([?!.,:@-])", r"\1", res)


def detect_mixed_language(text: str) -> dict:
    """Detect presence of multiple scripts and code-switching in a sentence."""
    scripts = {"latin": 0, "devanagari": 0, "gujarati": 0, "bengali": 0, "tamil": 0, "telugu": 0, "arabic_urdu": 0}
    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A:
            scripts["latin"] += 1
        elif 0x0900 <= cp <= 0x097F:
            scripts["devanagari"] += 1
        elif 0x0A80 <= cp <= 0x0AFF:
            scripts["gujarati"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            scripts["bengali"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            scripts["tamil"] += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            scripts["telugu"] += 1
        elif 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
            scripts["arabic_urdu"] += 1

    active_scripts = [s for s, count in scripts.items() if count > 0]
    is_mixed = len(active_scripts) > 1
    primary = max(scripts, key=scripts.get) if any(scripts.values()) else "latin"

    return {
        "is_mixed": is_mixed,
        "primary_script": primary,
        "active_scripts": active_scripts,
        "char_counts": scripts,
    }


def tokenize(text: str) -> list[str]:
    """Script-aware tokenization handling alphanumeric, punctuation, and Indic words."""
    norm = normalize(text).lower()
    # Match contiguous word tokens (letters, digits, combining marks, apostrophe)
    tokens = []
    cur = []
    for ch in norm:
        cat = unicodedata.category(ch)
        # Letter, Mark (matra/halant/nukta), Number, or internal apostrophe
        if cat[0] in ("L", "M", "N") or ch == "'":
            cur.append(ch)
        elif cur:
            tokens.append("".join(cur))
            cur = []
    if cur:
        tokens.append("".join(cur))
    return tokens


def remove_stopwords(tokens: list[str], lang: str = "en") -> list[str]:
    """Language-aware stopword removal. Handles Hinglish and mixed languages cleanly."""
    sw = set(STOPWORDS.get(lang, set()))
    if lang == "hinglish":
        sw = sw.union(STOPWORDS.get("hinglish", set())).union(STOPWORDS.get("en", set()))

    filtered = [t for t in tokens if t.lower() not in sw]
    return filtered


def stem(token: str, lang: str = "en") -> str:
    """Language-aware stemmer.

    Applies morphological suffix stripping strictly to English tokens.
    Indic words pass through safely to preserve inflectional intent markers
    (e.g. 'बजाओ' vs 'बजाना', 'वाजले' vs 'वाजवा'), as empirically verified.
    """
    # Indic words pass through un-mutilated
    if not token.isascii():
        return token

    # Only apply English suffix stripping to English / Latin tokens >= 5 chars
    if len(token) <= 4:
        return token

    for suf in _EN_SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            base = token[:-len(suf)]
            if len(base) > 3 and base[-1] == base[-2] and base[-1] not in "aeiouls":
                base = base[:-1]  # running -> runn -> run
            return base
    return token


def preprocess(text: str, lang: str = "en") -> dict:
    """Run full NLP preprocessing pipeline returning every intermediate stage.

    Guarantees:
    - Original input is preserved under 'original' without mutation.
    - Normalized string copy under 'normalized'.
    - Safe Hinglish normalization under 'hinglish_normalized'.
    - Tokens, stopwords removed, and stems.
    - Mixed-language breakdown under 'mixed_language'.
    """
    raw_original = str(text or "")
    expanded = expand_contractions(raw_original)
    norm = normalize(expanded)
    mixed_meta = detect_mixed_language(raw_original)

    # If Hinglish or mixed with Latin, produce normalized Hinglish text
    is_hinglish_or_mixed = (lang == "hinglish") or (mixed_meta["is_mixed"] and mixed_meta["char_counts"]["latin"] > 0)
    hinglish_norm = normalize_hinglish_text(norm) if is_hinglish_or_mixed else norm

    # Tokenize the normalized text
    tokens = tokenize(hinglish_norm if lang == "hinglish" else norm)
    filtered = remove_stopwords(tokens, lang)
    stems = [stem(t, lang) for t in filtered]

    return {
        "original": raw_original,
        "normalized": norm,
        "hinglish_normalized": hinglish_norm,
        "tokens": tokens,
        "without_stopwords": filtered,
        "stems": stems,
        "is_mixed": mixed_meta["is_mixed"],
        "primary_script": mixed_meta["primary_script"],
        "active_scripts": mixed_meta["active_scripts"],
    }
