"""Text preprocessing: normalisation, tokenisation, stop-word removal, stemming."""
import re
import unicodedata

STOPWORDS = {
    "en": set("a an the is are was were am be been to of in on at for and or but if so it this that "
              "i you he she we they me my your our their with as by from do does did have has had".split()),
    "hi": set("है हैं था थे थी का की के को में से पर और या यह वह मैं तुम आप हम एक भी तो ही कर".split()),
    "mr": set("आहे आहेत होते आणि किंवा हा ही हे तो ती ते मी तू तुम्ही मला तुला का काय या त्या".split()),
    "gu": set("છે છું છો હતા અને કે આ તે હું તું તમે મને તને શું ના માં થી નો ની નું".split()),
    "es": set("el la los las un una de del en y o que es son por para con".split()),
    "fr": set("le la les un une des de du en et ou que est sont pour avec dans".split()),
    "de": set("der die das ein eine und oder ist sind zu von mit in auf für".split()),
}

def _keep(ch: str) -> bool:
    """Keep letters, combining marks (Devanagari matras etc.), digits, whitespace and light punctuation."""
    cat = unicodedata.category(ch)
    return cat[0] in "LMN" or ch.isspace() or ch in "'?!.,:@-"


def _is_word_char(ch: str) -> bool:
    return unicodedata.category(ch)[0] in "LMN" or ch == "'"

_SUFFIXES = ("ingly", "edly", "ing", "ed", "ly", "es", "s")


def normalize(text: str) -> str:
    """Unicode-normalise, collapse whitespace, strip URLs/emoji-noise."""
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"https?://\S+", " ", text)
    text = "".join(ch if _keep(ch) else " " for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str):
    tokens, cur = [], []
    for ch in normalize(text).lower():
        if _is_word_char(ch):
            cur.append(ch)
        elif cur:
            tokens.append("".join(cur)); cur = []
    if cur:
        tokens.append("".join(cur))
    return tokens


def remove_stopwords(tokens, lang="en"):
    sw = STOPWORDS.get(lang, set())
    return [t for t in tokens if t not in sw]


def stem(token: str) -> str:
    """Light suffix-stripping stemmer (English only; other scripts pass through)."""
    if not token.isascii() or len(token) <= 4:
        return token
    for suf in _SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            base = token[: -len(suf)]
            if len(base) > 3 and base[-1] == base[-2] and base[-1] not in "aeiouls":
                base = base[:-1]  # running -> runn -> run
            return base
    return token


def preprocess(text: str, lang="en") -> dict:
    """Run the full pipeline and return every intermediate stage (shown in the UI)."""
    norm = normalize(text)
    tokens = tokenize(norm)
    filtered = remove_stopwords(tokens, lang)
    stems = [stem(t) for t in filtered]
    return {"normalized": norm, "tokens": tokens, "without_stopwords": filtered, "stems": stems}
