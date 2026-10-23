"""One-time extraction of every base64 image embedded in the legacy catalog HTML.

Usage:
    python tools/extract_legacy.py ref/2025-10-15_catalog_monochrome.html --out assets_src/legacy

Writes:
    <out>/products/<key>.webp         every key of the `var IMG={...}` map
    <out>/banners/hero.webp, band_<family>.webp
    <out>/images/logo_top.webp, logo_footer.webp, spread_<name>.webp
    <out>/legacy_index.json           {name: {file, sha1, w, h, used_in}}
    assets_src/required_keys.txt      every data-img key the markup references
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import config  # noqa: E402

DATA_RE = r"data:image/webp;base64,[A-Za-z0-9+/=]+"


def _decode(uri: str) -> bytes:
    return base64.b64decode(uri.split(",", 1)[1])


def _write(out: Path, rel: str, data: bytes, used_in: str, index: dict) -> None:
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    im = Image.open(io.BytesIO(data))
    index[Path(rel).stem] = {
        "file": rel,
        "sha1": hashlib.sha1(data).hexdigest(),
        "w": im.size[0],
        "h": im.size[1],
        "mode": im.mode,
        "used_in": used_in,
    }


def extract(html_path: Path, out: Path) -> dict:
    html = html_path.read_text(encoding="utf-8")
    index: dict = {}

    m = re.search(r"var IMG=(\{.*?\});", html, re.S)
    if not m:
        raise SystemExit("IMG map not found")
    img_map = json.loads(m.group(1))
    for key, uri in img_map.items():
        _write(out, f"products/{key}.webp", _decode(uri), "IMG", index)

    hero = re.search(r'<section class="hero" style="--img:url\((%s)\)"' % DATA_RE, html)
    if hero:
        _write(out, "banners/hero.webp", _decode(hero.group(1)), "style", index)
    band_re = r'<section class="family" id="(\w+)">\s*<header class="band" style="--img:url\((%s)\)"' % DATA_RE
    for fam, uri in re.findall(band_re, html):
        _write(out, f"banners/band_{fam}.webp", _decode(uri), "style", index)

    top = re.search(r'<img class="logo" src="(%s)"' % DATA_RE, html)
    if top:
        _write(out, "images/logo_top.webp", _decode(top.group(1)), "img", index)
    for name, uri in re.findall(r'<figure class="f-(\w+)"><img src="(%s)"' % DATA_RE, html):
        _write(out, f"images/spread_{name}.webp", _decode(uri), "img", index)
    foot = re.search(r'<div class="full flogo"><img src="(%s)"' % DATA_RE, html)
    if foot:
        _write(out, "images/logo_footer.webp", _decode(foot.group(1)), "img", index)

    (out / "legacy_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
    )

    refs = sorted({k for k in re.findall(r'data-img="([^"]*)"', html) if k})
    config.REQUIRED_KEYS.parent.mkdir(parents=True, exist_ok=True)
    config.REQUIRED_KEYS.write_text("\n".join(refs) + "\n", encoding="utf-8")

    n_style = sum(1 for v in index.values() if v["used_in"] == "style")
    n_img = sum(1 for v in index.values() if v["used_in"] == "img")
    leftover = len(re.findall(DATA_RE, html)) - len(index)
    print(
        f"products={len(img_map)} banners={n_style} images={n_img} "
        f"required_keys={len(refs)} unaccounted_data_uris={leftover}"
    )
    return index


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path)
    ap.add_argument("--out", type=Path, default=config.LEGACY)
    args = ap.parse_args()
    config.assert_safe_output(args.out)
    extract(args.html, args.out)


if __name__ == "__main__":
    main()
