"""Group resolved verses onto slides without changing the wording."""

from __future__ import annotations

from slides.config import ATTRIBUTION_BOTH, ATTRIBUTION_ENGLISH
from slides.models import ResolvedVerse, SlideVerse

MAX_COMBINED_CHARS = 650
LanguageMode = str


def _visible(verse: ResolvedVerse, language: LanguageMode) -> bool:
    if language == "english":
        return bool(verse.english)
    if language == "urdu":
        return bool(verse.urdu)
    return bool(verse.english or verse.urdu)


def _length_of(verse: ResolvedVerse, language: LanguageMode) -> int:
    parts: list[str] = []
    if language != "urdu" and verse.english:
        parts.append(verse.english)
    if language != "english" and verse.urdu:
        parts.append(verse.urdu)
    return len(" ".join(parts))


def _join_field(verses: list[ResolvedVerse], field: str) -> str | None:
    lines: list[str] = []
    for verse in verses:
        text = getattr(verse, field)
        if not text:
            continue
        lines.append(text if len(verses) == 1 else f"{verse.verse}  {text}")
    return "\n".join(lines) if lines else None


def _cite(verses: list[ResolvedVerse], language: LanguageMode) -> str:
    name = verses[0].book_name_urdu if language == "urdu" else verses[0].book_name
    first = verses[0].verse
    last = verses[-1].verse
    chapter = verses[0].chapter
    if len(verses) == 1 or first == last:
        return f"{name} {chapter}:{first}"
    return f"{name} {chapter}:{first}-{last}"


def _to_slide(verses: list[ResolvedVerse], language: LanguageMode) -> SlideVerse:
    english = None if language == "urdu" else _join_field(verses, "english")
    urdu = None if language == "english" else _join_field(verses, "urdu")
    if urdu:
        attribution = ATTRIBUTION_BOTH
    elif english:
        attribution = ATTRIBUTION_ENGLISH
    else:
        attribution = None
    return SlideVerse(reference=_cite(verses, language), english=english, urdu=urdu, attribution=attribution)


def group_into_slides(verses: list[ResolvedVerse], language: LanguageMode, keep_together: bool) -> list[SlideVerse]:
    usable = [verse for verse in verses if _visible(verse, language)]
    if not keep_together:
        return [_to_slide([verse], language) for verse in usable]

    groups: list[list[ResolvedVerse]] = []
    for verse in usable:
        current = groups[-1] if groups else None
        previous = current[-1] if current else None
        contiguous = bool(
            previous
            and previous.book_id == verse.book_id
            and previous.chapter == verse.chapter
            and verse.verse == previous.verse + 1
        )
        if not current or not contiguous:
            groups.append([verse])
        else:
            current.append(verse)

    slides: list[SlideVerse] = []
    for group in groups:
        chunk: list[ResolvedVerse] = []
        chars = 0

        def flush() -> None:
            nonlocal chunk, chars
            if chunk:
                slides.append(_to_slide(chunk, language))
            chunk = []
            chars = 0

        for verse in group:
            length = _length_of(verse, language)
            if chunk and chars + length > MAX_COMBINED_CHARS:
                flush()
            chunk.append(verse)
            chars += length
        flush()
    return slides
