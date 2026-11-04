"""Search the bundled Bibles. Latin text searches English. Urdu script searches Urdu."""

from __future__ import annotations

import re
import threading

from slides.books import load_books
from slides.lookup import _chapter
from slides.models import SearchHit
from slides.normalize import english_keys, preview_text, tokenize_english, tokenize_urdu

_lock = threading.Lock()
_ready = False
_books: dict[int, tuple[str, str]] = {}
_english: dict[str, list[int]] = {}
_urdu: dict[str, list[int]] = {}
_preview_en: dict[int, str] = {}
_preview_ur: dict[int, str] = {}


def pack_verse_id(book_id: int, chapter: int, verse: int) -> int:
    return book_id * 1_000_000 + chapter * 1_000 + verse


def unpack_verse_id(verse_id: int) -> tuple[int, int, int]:
    book_id = verse_id // 1_000_000
    remainder = verse_id % 1_000_000
    return book_id, remainder // 1_000, remainder % 1_000


def _add(postings: dict[str, list[int]], keys: list[str], verse_id: int) -> None:
    for key in keys:
        bucket = postings.get(key)
        if bucket is None:
            postings[key] = [verse_id]
        elif bucket[-1] != verse_id:
            bucket.append(verse_id)


def ensure_index() -> None:
    global _ready
    if _ready:
        return
    with _lock:
        if _ready:
            return
        for book in load_books():
            _books[book.id] = (book.name_english, book.name_urdu)
            for chapter in range(1, book.chapter_count + 1):
                english = _chapter("en", book.id, chapter)
                urdu = _chapter("ur", book.id, chapter)
                urdu_by_verse = {int(item["verse"]): str(item["text"]) for item in urdu.get("verses", [])}
                seen_urdu: set[int] = set()
                for item in english.get("verses", []):
                    number = int(item["verse"])
                    verse_id = pack_verse_id(book.id, chapter, number)
                    tokens = set(tokenize_english(str(item["text"])))
                    for token in tokens:
                        _add(_english, english_keys(token), verse_id)
                    _preview_en[verse_id] = preview_text(str(item["text"]))
                    urdu_text = urdu_by_verse.get(number)
                    if not urdu_text:
                        continue
                    seen_urdu.add(number)
                    for token in set(tokenize_urdu(urdu_text)):
                        _add(_urdu, [token], verse_id)
                    _preview_ur[verse_id] = preview_text(urdu_text)
                for item in urdu.get("verses", []):
                    number = int(item["verse"])
                    if number in seen_urdu:
                        continue
                    verse_id = pack_verse_id(book.id, chapter, number)
                    for token in set(tokenize_urdu(str(item["text"]))):
                        _add(_urdu, [token], verse_id)
                    _preview_ur[verse_id] = preview_text(str(item["text"]))
        _ready = True


def query_index(raw: str, limit: int = 50) -> tuple[list[SearchHit], int, bool]:
    urdu = bool(re.search(r"[\u0600-\u06FF]", raw))
    tokens = tokenize_urdu(raw) if urdu else tokenize_english(raw)
    if not tokens:
        return [], 0, True
    ensure_index()
    postings = _urdu if urdu else _english
    previews = _preview_ur if urdu else _preview_en
    ids: set[int] | None = None
    for token in tokens:
        union: set[int] = set()
        keys = [token] if urdu else english_keys(token)
        for key in keys:
            union.update(postings.get(key, []))
        ids = union if ids is None else ids & union
    ordered = sorted(ids or [])
    hits: list[SearchHit] = []
    for verse_id in ordered[:limit]:
        book_id, chapter, verse = unpack_verse_id(verse_id)
        names = _books.get(book_id, ("Verse", "Verse"))
        name = names[1] if urdu else names[0]
        hits.append(
            SearchHit(
                book_id=book_id,
                chapter=chapter,
                verse=verse,
                reference=f"{name} {chapter}:{verse}",
                preview=previews.get(verse_id, ""),
                language="urdu" if urdu else "english",
            )
        )
    return hits, len(ordered), False
