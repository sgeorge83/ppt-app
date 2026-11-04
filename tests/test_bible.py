import zipfile
from pathlib import Path

import pytest
from PIL import Image

from slides.export_pptx import export_pptx
from slides.lookup import resolve_passages
from slides.parser import parse_reference_string
from slides.paths import bible_text_ready
from slides.search import query_index

WEB = "For God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life."
URDU = "کیونکہ اللہ نے دنیا سے اِتنی محبت رکھی کہ اُس نے اپنے اکلوتے فرزند کو بخش دیا، تاکہ جو بھی اُس پر ایمان لائے ہلاک نہ ہو بلکہ ابدی زندگی پائے۔"

pytestmark = pytest.mark.skipif(not bible_text_ready(), reason="Bible text is cloned by the GitHub build.")


def test_john_316_wording_is_copied():
    verses = resolve_passages(parse_reference_string("John 3:16"))
    assert len(verses) == 1
    assert verses[0].english == WEB
    assert verses[0].urdu == URDU
    assert verses[0].book_name_urdu == "یوحنا"


def test_urdu_book_name_parses():
    specs = parse_reference_string("یوحنا 3:16")
    assert specs[0].book_id == 43
    assert specs[0].chapter == 3
    assert specs[0].verse_start == 16


def test_love_search_includes_john_316():
    hits, _total, empty = query_index("love", limit=2000)
    assert empty is False
    assert any(hit.book_id == 43 and hit.chapter == 3 and hit.verse == 16 for hit in hits)


def test_pptx_contains_both_wordings_and_rtl(tmp_path: Path):
    verses = resolve_passages(parse_reference_string("John 3:16"))
    logo = tmp_path / "logo.png"
    Image.new("RGB", (32, 32), (201, 168, 76)).save(logo)
    target = tmp_path / "john.pptx"
    export_pptx(
        verses,
        target,
        language="both",
        theme_id="air",
        church_name="WordOnAir Chapel",
        logo_path=str(logo),
    )
    with zipfile.ZipFile(target) as package:
        slides = [name for name in package.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        xml = "\n".join(package.read(name).decode("utf-8") for name in slides)
        media = [name for name in package.namelist() if name.startswith("ppt/media/")]
    assert WEB in xml
    assert URDU in xml
    assert "Urdu Geo Version · World English Bible" in xml
    assert "WordOnAir Chapel" in xml
    assert 'rtl="1"' in xml
    assert media
