"""Load a passage with both wordings side by side."""

from __future__ import annotations

import json
from functools import lru_cache

from slides.books import load_books
from slides.models import PassageSpec, ResolvedVerse
from slides.paths import english_dir, urdu_dir


@lru_cache(maxsize=256)
def _chapter(language: str, book_id: int, chapter: int) -> dict:
    root = english_dir() if language == "en" else urdu_dir()
    path = root / "chapters" / str(book_id) / f"{chapter}.json"
    if not path.is_file():
        name = "English" if language == "en" else "Urdu"
        raise FileNotFoundError(f"Could not load the {name} text for book {book_id}, chapter {chapter}.")
    return json.loads(path.read_text(encoding="utf-8"))


def _verse_map(chapter: dict) -> dict[int, str]:
    return {int(item["verse"]): str(item["text"]) for item in chapter.get("verses", [])}


def _max_verse(chapter: dict) -> int:
    verses = [int(item["verse"]) for item in chapter.get("verses", [])]
    counted = int(chapter.get("verse_count") or 0)
    return max([counted, *verses], default=0)


def resolve_passages(specs: list[PassageSpec]) -> list[ResolvedVerse]:
    if not specs:
        raise ValueError("Enter a reference such as John 3:16.")
    books = {book.id: book for book in load_books()}
    verses: list[ResolvedVerse] = []
    for spec in specs:
        english_chapter = _chapter("en", spec.book_id, spec.chapter)
        urdu_chapter = _chapter("ur", spec.book_id, spec.chapter)
        book = books.get(spec.book_id)
        english_name = book.name_english if book else spec.book_name
        urdu_name = book.name_urdu if book else str(urdu_chapter.get("book_name") or spec.book_name)
        english_verses = _verse_map(english_chapter)
        urdu_verses = _verse_map(urdu_chapter)
        last = max(_max_verse(english_chapter), _max_verse(urdu_chapter))
        end = spec.verse_end if spec.verse_end is not None else last
        if spec.verse_start > last:
            raise ValueError(f"{english_name} {spec.chapter} only has {last} verses.")
        for number in range(spec.verse_start, min(end, last) + 1):
            english = english_verses.get(number)
            urdu = urdu_verses.get(number)
            if not english and not urdu:
                continue
            verses.append(
                ResolvedVerse(
                    book_id=spec.book_id,
                    book_name=english_name,
                    book_name_urdu=urdu_name,
                    chapter=spec.chapter,
                    verse=number,
                    english=english,
                    urdu=urdu,
                    reference=f"{english_name} {spec.chapter}:{number}",
                )
            )
    if not verses:
        raise ValueError("Those verses were not found.")
    return verses
