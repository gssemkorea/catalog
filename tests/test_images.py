import pytest
from PIL import Image

from tools import config


def _open(rel):
    return Image.open(config.STATIC / rel)


def test_product_variants(manifest):
    for key, e in manifest["products"].items():
        t, m, f = _open(e["t"]), _open(e["m"]), _open(e["f"])
        assert t.width == min(config.PRODUCT_WIDTHS["t"], e["w"]), key
        assert m.width == min(config.PRODUCT_WIDTHS["m"], e["w"]), key
        assert f.width <= config.FULL_MAX, key
        if e.get("alpha"):
            for im in (t, m, f):
                assert "A" in im.getbands(), f"{key}: alpha lost"
        assert e["tw"] == t.width and e["mw"] == m.width and e["fw"] == f.width


def test_banner_shape_and_grayscale(manifest):
    for name, e in manifest["banners"].items():
        ratio = config.HERO_RATIO if name == "hero" else config.BANNER_RATIO
        for v in ("lg", "md"):
            im = _open(e[v]).convert("RGB")
            assert abs(im.width / im.height - ratio) < 0.02, (name, v, im.size)
            assert im.width <= (config.HERO_WIDTHS if name == "hero" else config.BANNER_WIDTHS)[v]
            px = list(im.resize((32, 32)).get_flattened_data())
            assert max(max(abs(r - g), abs(g - b)) for r, g, b in px) <= 4, f"{name} {v} not grayscale"


def test_logo_is_white_with_alpha(manifest):
    im = _open(manifest["images"]["logo"]["p"])
    assert im.format == "PNG" and "A" in im.getbands()
    px = [c for c in im.convert("RGBA").get_flattened_data() if c[3] > 128]
    nonwhite = sum(1 for c in px if min(c[:3]) < 200) / len(px)
    assert nonwhite < 0.01, f"{nonwhite:.1%} non-white opaque pixels"


def test_mirror_is_flipped(manifest):
    e = manifest["products"].get("160-0000")
    if not e or not e.get("mirrored"):
        pytest.skip("no mirrored key")
    base = manifest["products"]["160-1000"]
    assert (e["w"], e["h"]) == (base["w"], base["h"])
