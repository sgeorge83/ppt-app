"""Verse and slide records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PassageSpec:
    book_id: int
    book_name: str
    chapter: int
    verse_start: int
    verse_end: int | None
    label: str


@dataclass(frozen=True)
class BookMeta:
    id: int
    name_english: str
    name_urdu: str
    chapter_count: int


@dataclass(frozen=True)
class ResolvedVerse:
    book_id: int
    book_name: str
    book_name_urdu: str
    chapter: int
    verse: int
    english: str | None
    urdu: str | None
    reference: str


@dataclass(frozen=True)
class SlideVerse:
    reference: str
    english: str | None
    urdu: str | None
    attribution: str | None


@dataclass(frozen=True)
class SearchHit:
    book_id: int
    chapter: int
    verse: int
    reference: str
    preview: str
    language: str
