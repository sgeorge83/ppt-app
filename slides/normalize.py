"""Token rules shared by English and Urdu search."""

from __future__ import annotations

import re

ENGLISH_STOP = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for", "with", "as", "at", "by",
    "from", "that", "this", "these", "those", "is", "are", "was", "were", "be", "been", "am", "it",
    "its", "he", "she", "they", "them", "his", "her", "their", "you", "your", "we", "our", "do",
    "did", "does", "have", "has", "had", "will", "shall", "into", "over", "after", "before", "about",
    "than", "then", "so", "if", "when", "who", "whom", "which", "what", "there", "here", "all",
    "also", "just", "unto", "ye", "thou", "thee", "thy", "thine", "hath", "shalt", "him", "me", "my",
    "i", "o",
}

_URDU_STOP_RAW = [
    "کے", "کی", "کا", "کو", "نے", "میں", "سے", "پر", "ہے", "ہیں", "ہوں", "تھا", "تھی", "تھے",
    "اور", "یا", "یہ", "وہ", "ان", "اس", "کہ", "جو", "بھی", "ہی", "تو", "نہ", "نہیں", "گیا",
    "گئی", "گئے", "ایک", "کیا", "کر", "لیے", "لئے", "ہو", "ہوا", "ہوئی", "اپنے", "اپنی", "اپنا",
    "جس", "جن", "اگر", "تاکہ", "بلکہ", "بعد", "پہلے",
]


def strip_arabic_marks(text: str) -> str:
    return re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u200C\u200D]", "", text)


def normalize_urdu_token(text: str) -> str:
    cleaned = strip_arabic_marks(text)
    cleaned = re.sub(r"[يى]", "ی", cleaned)
    cleaned = cleaned.replace("ك", "ک")
    cleaned = re.sub(r"[ۀہة]", "ہ", cleaned)
    cleaned = re.sub(r"[أإآ]", "ا", cleaned)
    cleaned = cleaned.replace("ؤ", "و")
    return cleaned.replace("ئ", "ی")


URDU_STOP = {normalize_urdu_token(word) for word in _URDU_STOP_RAW}


def tokenize_english(text: str) -> list[str]:
    lowered = text.lower()
    lowered = re.sub(r"['’]s\b", "", lowered)
    lowered = re.sub(r"['’]", "", lowered)
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return [
        token
        for token in lowered.split()
        if len(token) >= 2 and token not in ENGLISH_STOP and not token.isdigit()
    ]


def tokenize_urdu(text: str) -> list[str]:
    cleaned = normalize_urdu_token(text)
    cleaned = re.sub(r"[^\u0600-\u06FF\s]", " ", cleaned)
    return [token for token in cleaned.split() if len(token) >= 2 and token not in URDU_STOP]


def english_keys(token: str) -> list[str]:
    keys = {token}
    if len(token) >= 5 and re.search(r"[sd]$", token) and not token.endswith("ss"):
        stem = token[:-1]
        if len(stem) >= 4:
            keys.add(stem)
    return list(keys)


def preview_text(text: str, limit: int = 100) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    chars = list(clean)
    if len(chars) <= limit:
        return clean
    return "".join(chars[:limit]) + "…"
