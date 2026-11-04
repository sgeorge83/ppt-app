"""Write sermon slides into a PowerPoint file."""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from slides.grouping import group_into_slides
from slides.models import ResolvedVerse, SlideVerse
from slides.themes import Theme, get_theme


def _rgb(value: str) -> RGBColor:
    return RGBColor.from_string(value.removeprefix("#"))


def _blank_layout(presentation: Presentation):
    for layout in presentation.slide_layouts:
        if layout.name.lower() == "blank":
            return layout
    return presentation.slide_layouts[len(presentation.slide_layouts) - 1]


def _set_run_font(run, name: str, size: int, color: str, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)
    r_pr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:cs", "a:ea"):
        element = r_pr.find(qn(tag))
        if element is None:
            element = etree.SubElement(r_pr, qn(tag))
        element.set("typeface", name)


def _write_lines(text_frame, text: str, font_name: str, size: int, color: str, *, bold: bool = False, rtl: bool = False) -> None:
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.auto_size = None
    lines = text.split("\n") if text else [""]
    for index, line in enumerate(lines):
        paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
        paragraph.alignment = PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT
        paragraph.space_after = Pt(6)
        if rtl:
            properties = paragraph._p.get_or_add_pPr()
            properties.set("rtl", "1")
            properties.set("algn", "r")
        run = paragraph.add_run()
        run.text = line
        _set_run_font(run, font_name, size, color, bold)


def _add_textbox(slide, left, top, width, height, text: str, font_name: str, size: int, color: str, *, bold: bool = False, rtl: bool = False):
    shape = slide.shapes.add_textbox(left, top, width, height)
    shape.text_frame.word_wrap = True
    _write_lines(shape.text_frame, text, font_name, size, color, bold=bold, rtl=rtl)
    return shape


def _paint_slide(slide, content: SlideVerse, theme: Theme, church_name: str, logo_path: str | None, width: int, height: int) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(theme.background)

    margin = Inches(0.55)
    content_width = width - Inches(1.1) - (Inches(1.15) if logo_path else 0)
    if logo_path and Path(logo_path).is_file():
        slide.shapes.add_picture(str(logo_path), width - Inches(1.45), Inches(0.32), height=Inches(0.82))

    cursor = Inches(0.38)
    if church_name.strip():
        _add_textbox(slide, margin, cursor, content_width, Inches(0.38), church_name.strip(), theme.font, 16, theme.muted, bold=True)
        cursor += Inches(0.36)

    _add_textbox(slide, margin, cursor, content_width, Inches(0.55), content.reference, theme.font, 28, theme.accent, bold=True)
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, margin, cursor + Inches(0.58), Inches(1.8), Pt(4))
    rule.fill.solid()
    rule.fill.fore_color.rgb = _rgb(theme.accent)
    rule.line.fill.background()
    cursor += Inches(0.78)

    bottom = height - Inches(0.62)
    body_height = bottom - cursor - Inches(0.08)
    has_urdu = bool(content.urdu)
    has_english = bool(content.english)
    if has_urdu and has_english:
        urdu_height = int(body_height * 0.46)
        _add_textbox(slide, margin, cursor, content_width, urdu_height, content.urdu or "", theme.urdu_font, 24, theme.text, rtl=True)
        _add_textbox(
            slide,
            margin,
            cursor + urdu_height,
            content_width,
            body_height - urdu_height,
            content.english or "",
            theme.font,
            20,
            theme.text,
        )
    elif has_urdu:
        _add_textbox(slide, margin, cursor, content_width, body_height, content.urdu or "", theme.urdu_font, 28, theme.text, rtl=True)
    else:
        _add_textbox(slide, margin, cursor, content_width, body_height, content.english or "", theme.font, 24, theme.text)

    if content.attribution:
        _add_textbox(
            slide,
            margin,
            height - Inches(0.48),
            width - Inches(1.1),
            Inches(0.32),
            content.attribution,
            theme.font,
            12,
            theme.muted,
        )


def export_pptx(
    verses: list[ResolvedVerse],
    destination: str | Path,
    *,
    language: str = "both",
    keep_together: bool = False,
    theme_id: str = "air",
    church_name: str = "",
    logo_path: str | None = None,
    existing: str | Path | None = None,
) -> Path:
    slides = group_into_slides(verses, language, keep_together)
    if not slides:
        raise ValueError("No verse text is available in that language.")
    theme = get_theme(theme_id)
    if existing:
        presentation = Presentation(str(existing))
    else:
        presentation = Presentation()
        presentation.slide_width = Inches(13.333)
        presentation.slide_height = Inches(7.5)
    layout = _blank_layout(presentation)
    for content in slides:
        slide = presentation.slides.add_slide(layout)
        _paint_slide(
            slide,
            content,
            theme,
            church_name,
            logo_path,
            presentation.slide_width,
            presentation.slide_height,
        )
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(target))
    return target
