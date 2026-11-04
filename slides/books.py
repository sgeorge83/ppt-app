"""Book lists for the two bundled Bibles."""

from __future__ import annotations

import json

from slides.models import BookMeta
from slides.normalize import strip_arabic_marks
from slides.parser import register_book_aliases
from slides.paths import bible_text_ready, english_dir, urdu_dir

_books: list[BookMeta] | None = None


def load_books() -> list[BookMeta]:
    global _books
    if _books is not None:
        return _books
    if not bible_text_ready():
        raise FileNotFoundError(
            "The Bible text is not installed beside WordOnAir Slides. "
            "The package should include the World English Bible and the Urdu Geo Version."
        )
    english = json.loads((english_dir() / "books.json").read_text(encoding="utf-8"))
    urdu = json.loads((urdu_dir() / "books.json").read_text(encoding="utf-8"))
    english_by_id = {int(book["id"]): book for book in english}
    books: list[BookMeta] = []
    for urdu_book in sorted(urdu, key=lambda item: int(item["id"])):
        book_id = int(urdu_book["id"])
        english_book = english_by_id.get(book_id)
        if english_book is None:
            raise FileNotFoundError(f"The English Bible is missing book {book_id}.")
        books.append(
            BookMeta(
                id=book_id,
                name_english=str(english_book["name"]),
                name_urdu=str(urdu_book["name"]),
                chapter_count=int(english_book["chapter_count"]),
            )
        )
    aliases: list[tuple[int, str]] = []
    for book in books:
        plain_urdu = strip_arabic_marks(book.name_urdu)
        patterns = [book.name_english, book.name_urdu]
        if plain_urdu != book.name_urdu:
            patterns.append(plain_urdu)
        aliases.extend((book.id, pattern) for pattern in patterns)
    register_book_aliases(aliases)
    _books = books
    return books


def ensure_book_aliases() -> None:
    if bible_text_ready():
        load_books()


def clear_book_cache() -> None:
    global _books
    _books = None
