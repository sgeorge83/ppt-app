"""Slide themes carried from the WordOnAir task pane."""

from __future__ import annotations

from dataclasses import dataclass

from slides.config import URDU_FONT


@dataclass(frozen=True)
class Theme:
    id: str
    name: str
    background: str
    text: str
    accent: str
    muted: str
    font: str
    urdu_font: str


THEMES: tuple[Theme, ...] = (
    Theme("air", "Morning Air", "#F4F7FB", "#152238", "#C9A84C", "#5C6E86", "Calibri", URDU_FONT),
    Theme("parchment", "Parchment", "#F3EFE4", "#2A261C", "#8A6430", "#6E675C", "Calibri", URDU_FONT),
    Theme("linen", "Linen", "#F7F5F2", "#1E2A3A", "#2F7A72", "#5E6974", "Calibri", URDU_FONT),
    Theme("chapel", "Chapel", "#EEF1F4", "#152238", "#152238", "#5A6573", "Georgia", URDU_FONT),
)

_LEGACY = {"midnight": "air", "sanctuary": "parchment", "light": "linen", "classic": "chapel"}


def get_theme(theme_id: str) -> Theme:
    resolved = theme_id if any(theme.id == theme_id for theme in THEMES) else _LEGACY.get(theme_id, "air")
    for theme in THEMES:
        if theme.id == resolved:
            return theme
    return THEMES[0]
