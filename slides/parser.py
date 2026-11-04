"""Bible reference parser. English abbreviations and Urdu book names share one lookup."""

from __future__ import annotations

import re

from slides.config import ENGLISH_BOOK_NAMES, EXTRA_ALIASES, SINGLE_CHAPTER_BOOK_IDS
from slides.models import PassageSpec

_dynamic_aliases: list[tuple[int, str]] = []
_lookup: list[tuple[int, str]] = []


def _rebuild_lookup() -> None:
    seen: set[str] = set()
    entries: list[tuple[int, str]] = []

    def add(book_id: int, pattern: str) -> None:
        trimmed = pattern.strip()
        key = trimmed.lower()
        if not trimmed or key in seen:
            return
        seen.add(key)
        entries.append((book_id, trimmed))

    for book_id, name in ENGLISH_BOOK_NAMES.items():
        add(book_id, name)
    for book_id, patterns in EXTRA_ALIASES.items():
        for pattern in patterns:
            add(book_id, pattern)
    for book_id, pattern in _dynamic_aliases:
        add(book_id, pattern)

    entries.sort(key=lambda item: (-len(item[1]), item[0]))
    _lookup.clear()
    _lookup.extend(entries)


def register_book_aliases(entries: list[tuple[int, str]]) -> None:
    global _dynamic_aliases
    _dynamic_aliases = list(entries)
    _rebuild_lookup()


def reset_book_aliases() -> None:
    register_book_aliases([])


_rebuild_lookup()


def _normalize_reference_input(value: str) -> str:
    text = value.replace("–", "-").replace("—", "-")
    text = re.sub(r"\b1st\b", "1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b2nd\b", "2", text, flags=re.IGNORECASE)
    text = re.sub(r"\b3rd\b", "3", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfirst\b", "1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bsecond\b", "2", text, flags=re.IGNORECASE)
    text = re.sub(r"\bthird\b", "3", text, flags=re.IGNORECASE)
    text = re.sub(r"(^|;|\band\b)\s*III\b", r"\1 3", text, flags=re.IGNORECASE)
    text = re.sub(r"(^|;|\band\b)\s*II\b", r"\1 2", text, flags=re.IGNORECASE)
    text = re.sub(r"(^|;|\band\b)\s*I\b", r"\1 1", text, flags=re.IGNORECASE)
    text = re.sub(r"([^\W\d_])\.", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _match_book(segment: str) -> tuple[int, str, str] | None:
    trimmed = segment.strip()
    for book_id, pattern in _lookup:
        matcher = re.compile(rf"^{re.escape(pattern)}(?:\s+|$)(.*)$", re.IGNORECASE)
        match = matcher.match(trimmed)
        if not match:
            continue
        book_name = ENGLISH_BOOK_NAMES.get(book_id, pattern)
        return book_id, book_name, (match.group(1) or "").strip()
    return None


def _whole_chapter(book_id: int, book_name: str, chapter: int) -> PassageSpec:
    return PassageSpec(book_id, book_name, chapter, 1, None, f"{book_name} {chapter}")


def _verse_spec(book_id: int, book_name: str, chapter: int, start: int, end: int) -> PassageSpec:
    label = f"{book_name} {chapter}:{start}" if start == end else f"{book_name} {chapter}:{start}-{end}"
    return PassageSpec(book_id, book_name, chapter, start, end, label)


def _parse_verse_list(book_id: int, book_name: str, chapter: int, verse_list: str) -> list[PassageSpec]:
    parts = [part.strip() for part in verse_list.split(",") if part.strip()]
    if not parts:
        raise ValueError(f"Could not read {book_name} {chapter}.")
    specs: list[PassageSpec] = []
    for part in parts:
        match = re.match(r"^(\d+)\s*-\s*(\d+)$", part) or re.match(r"^(\d+)$", part)
        if not match:
            raise ValueError(f"Could not read {book_name} {chapter}:{verse_list}.")
        start = int(match.group(1))
        end = int(match.group(2)) if match.lastindex and match.lastindex >= 2 and match.group(2) else start
        if start < 1 or end < start:
            raise ValueError(f"The verse range {part} is not valid.")
        specs.append(_verse_spec(book_id, book_name, chapter, start, end))
    return specs


def _parse_rest(book_id: int, book_name: str, rest: str) -> list[PassageSpec]:
    single = book_id in SINGLE_CHAPTER_BOOK_IDS
    if not rest:
        if not single:
            raise ValueError(f"Add a chapter, for example {book_name} 1.")
        spec = _whole_chapter(book_id, book_name, 1)
        return [PassageSpec(spec.book_id, spec.book_name, 1, 1, None, book_name)]

    match = re.match(r"^(\d+):(\d+)\s*-\s*(\d+):(\d+)$", rest)
    if match:
        start_chapter = int(match.group(1))
        start_verse = int(match.group(2))
        end_chapter = int(match.group(3))
        end_verse = int(match.group(4))
        if end_chapter < start_chapter or start_verse < 1 or end_verse < 1:
            raise ValueError("That reference range is not valid.")
        if start_chapter == end_chapter:
            return [_verse_spec(book_id, book_name, start_chapter, start_verse, end_verse)]
        specs = [
            PassageSpec(
                book_id,
                book_name,
                start_chapter,
                start_verse,
                None,
                f"{book_name} {start_chapter}:{start_verse}-",
            )
        ]
        for chapter in range(start_chapter + 1, end_chapter):
            specs.append(_whole_chapter(book_id, book_name, chapter))
        specs.append(_verse_spec(book_id, book_name, end_chapter, 1, end_verse))
        return specs

    match = re.match(r"^(\d+)\s*-\s*(\d+):(\d+)$", rest)
    if match and not single:
        start_chapter = int(match.group(1))
        end_chapter = int(match.group(2))
        end_verse = int(match.group(3))
        if end_chapter < start_chapter:
            raise ValueError("That chapter range is reversed.")
        specs = [_whole_chapter(book_id, book_name, chapter) for chapter in range(start_chapter, end_chapter)]
        specs.append(_verse_spec(book_id, book_name, end_chapter, 1, end_verse))
        return specs

    match = re.match(r"^(\d+):(.+)$", rest)
    if match:
        return _parse_verse_list(book_id, book_name, int(match.group(1)), match.group(2))

    match = re.match(r"^(\d+)\s*-\s*(\d+)$", rest)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        if end < start:
            raise ValueError("That range is reversed.")
        if single:
            return [_verse_spec(book_id, book_name, 1, start, end)]
        return [_whole_chapter(book_id, book_name, chapter) for chapter in range(start, end + 1)]

    match = re.match(r"^(\d+)$", rest)
    if match:
        number = int(match.group(1))
        if number < 1:
            raise ValueError("Chapter and verse numbers start at 1.")
        if single:
            return [_verse_spec(book_id, book_name, 1, number, number)]
        return [_whole_chapter(book_id, book_name, number)]

    raise ValueError(f"Could not read {book_name} {rest}.")


def parse_reference_string(reference: str, *, load_aliases: bool = True) -> list[PassageSpec]:
    if load_aliases:
        from slides.books import ensure_book_aliases

        ensure_book_aliases()
    if not reference or not reference.strip():
        raise ValueError("Enter a reference such as John 3:16.")
    segments = [
        part.strip()
        for part in re.split(r"\s*;\s*|\s+\band\b\s+", _normalize_reference_input(reference), flags=re.IGNORECASE)
        if part.strip()
    ]
    if not segments:
        raise ValueError("Enter a reference such as John 3:16.")
    specs: list[PassageSpec] = []
    for segment in segments:
        matched = _match_book(segment)
        if not matched:
            if re.search(r"[\u0600-\u06FF]", segment):
                raise ValueError(
                    "No Urdu book name matched. Install the bundled Bible text, then try the reference again."
                )
            raise ValueError(f'No Bible book found in "{segment}".')
        book_id, book_name, rest = matched
        specs.extend(_parse_rest(book_id, book_name, rest))
    return specs
