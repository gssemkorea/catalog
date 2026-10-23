import re

import pytest

from tools import config

INDEX = config.DIST / "index.html"
SINGLE = config.DIST / "Osteo-Fit_CMF_Catalog.html"
SINGLE_MAX_MB = 9.0

pytestmark = pytest.mark.skipif(not INDEX.exists(), reason="dist/ not frozen yet")


def _parse(html: str):
    html5lib = pytest.importorskip("html5lib")
    return html5lib.parse(html, namespaceHTMLElements=False)


def test_linked_export_is_relative_and_complete():
    html = INDEX.read_text(encoding="utf-8")
    assert '"/static' not in html and "url(/static" not in html
    refs = set(re.findall(r"""(?<![\w/])(static/[A-Za-z0-9_./@-]+)""", html))
    assert refs
    for rel in refs:
        assert (config.DIST / rel).exists(), rel
    doc = _parse(html)
    assert doc.find("head/title") is not None
    assert any(m.get("charset", "").lower() == "utf-8" for m in doc.iter("meta"))


@pytest.mark.skipif(not SINGLE.exists(), reason="single file not built")
def test_single_file_is_self_contained():
    html = SINGLE.read_text(encoding="utf-8")
    stripped = re.sub(r"data:[^\"')]+", "", html)
    assert "static/" not in stripped
    externals = set(re.findall(r"https?://([^/\"']+)", stripped))
    assert externals <= {"fonts.googleapis.com", "fonts.gstatic.com"}, externals
    assert SINGLE.stat().st_size / 1_048_576 <= SINGLE_MAX_MB
    _parse(html)
