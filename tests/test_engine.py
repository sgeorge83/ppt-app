from slides.models import ResolvedVerse
from slides.grouping import group_into_slides
from slides.normalize import english_keys
from slides.parser import parse_reference_string
from slides.search import pack_verse_id


def test_english_keys_stem_loved_to_love():
    assert "love" in english_keys("loved")


def test_reference_forms():
    john = parse_reference_string("John 3:16", load_aliases=False)
    assert john[0].book_id == 43
    assert john[0].chapter == 3
    assert john[0].verse_start == 16
    assert john[0].verse_end == 16

    short = parse_reference_string("Jn 3:16", load_aliases=False)
    assert short[0].book_id == 43

    psalm = parse_reference_string("Psalm 23", load_aliases=False)
    assert psalm[0].book_id == 19
    assert psalm[0].chapter == 23
    assert psalm[0].verse_end is None

    passage = parse_reference_string("1 Cor 13:4-7", load_aliases=False)
    assert passage[0].book_id == 46
    assert passage[0].verse_start == 4
    assert passage[0].verse_end == 7

    single = parse_reference_string("Jude 3", load_aliases=False)
    assert single[0].book_id == 65
    assert single[0].chapter == 1
    assert single[0].verse_start == 3


def test_pack_verse_id_round_trip():
    assert pack_verse_id(43, 3, 16) == 43_003_016


def _sample() -> list[ResolvedVerse]:
    return [
        ResolvedVerse(43, "John", "یوحنا", 3, 16, "For God so loved the world.", "محبت", "John 3:16"),
        ResolvedVerse(43, "John", "یوحنا", 3, 17, "For God didn't send his Son.", "بیٹا", "John 3:17"),
    ]


def test_group_keeps_wording_exact():
    slides = group_into_slides(_sample(), "english", False)
    assert len(slides) == 2
    assert slides[0].english == "For God so loved the world."
    assert slides[0].urdu is None
    assert slides[0].attribution == "World English Bible"


def test_group_bilingual_passage_and_urdu_reference():
    together = group_into_slides(_sample(), "both", True)
    assert len(together) == 1
    assert together[0].english == "16  For God so loved the world.\n17  For God didn't send his Son."
    assert "محبت" in (together[0].urdu or "")
    assert together[0].reference == "John 3:16-17"
    assert together[0].attribution == "Urdu Geo Version · World English Bible"
    urdu_only = group_into_slides(_sample(), "urdu", False)[0]
    assert urdu_only.reference == "یوحنا 3:16"
    assert urdu_only.english is None


def test_group_does_not_merge_a_gap():
    verses = _sample()
    skipped = [verses[0], ResolvedVerse(43, "John", "یوحنا", 3, 19, verses[1].english, verses[1].urdu, "John 3:19")]
    assert len(group_into_slides(skipped, "english", True)) == 2


def test_sample_pptx_marks_urdu_rtl(tmp_path):
    from slides.export_pptx import export_pptx
    import zipfile

    target = tmp_path / "sample.pptx"
    export_pptx(_sample(), target, language="both", keep_together=True, church_name="Grace Chapel")
    with zipfile.ZipFile(target) as package:
        xml = package.read("ppt/slides/slide1.xml").decode("utf-8")
    assert "For God so loved the world." in xml
    assert "محبت" in xml
    assert "Urdu Geo Version · World English Bible" in xml
    assert "Grace Chapel" in xml
    assert 'rtl="1"' in xml
