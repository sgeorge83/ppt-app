import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]


def test_chrome_engine_writes_a_powerpoint_file(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    subprocess.check_call(
        [sys.executable, "-c", "import build_chrome; build_chrome.write_blank(build_chrome.CHROME / 'blank.pptx')"],
        cwd=ROOT / "packaging",
    )
    target = tmp_path / "sample.pptx"
    env = os.environ.copy()
    env["CHROME_CHECK_PPTX"] = str(target)
    subprocess.check_call([node, "chrome/engine/check.mjs"], cwd=ROOT, env=env)
    presentation = Presentation(str(target))
    assert len(presentation.slides) == 1
    text = "\n".join(
        shape.text_frame.text
        for shape in presentation.slides[0].shapes
        if shape.has_text_frame
    )
    assert "For God so loved the world." in text
    assert "محبت" in text
    assert "Grace Chapel" in text
    assert 'rtl="1"' in presentation.slides[0]._element.xml
