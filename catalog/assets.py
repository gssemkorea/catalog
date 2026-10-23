"""Manifest loading and the `asset()` URL helper.

`asset()` deliberately does not use `url_for('static', ...)`: the frozen export must
work over file://, so the base is a plain config string ("/static" in dev, "static"
when freezing).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from flask import current_app

_HASHED = re.compile(r"\.[0-9a-f]{8}\.(webp|png|jpg|svg)$")
_hash_cache: dict[tuple[str, int], str] = {}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"version": 0, "products": {}, "banners": {}, "images": {}, "_missing": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_mtime_ns"] = path.stat().st_mtime_ns
    return data


def manifest() -> dict:
    return current_app.extensions["manifest"]


def static_hash(rel: str) -> str:
    """Short content hash of a file under the static folder (for ?v= busting)."""
    p = Path(current_app.static_folder) / rel
    try:
        key = (rel, p.stat().st_mtime_ns)
    except FileNotFoundError:
        return "0"
    if key not in _hash_cache:
        _hash_cache[key] = hashlib.sha1(p.read_bytes()).hexdigest()[:8]
    return _hash_cache[key]


def asset(rel: str, versioned: bool = True) -> str:
    base = current_app.config["ASSET_BASE"].rstrip("/")
    rel = rel.lstrip("/")
    if versioned and not _HASHED.search(rel):
        rel = f"{rel}?v={static_hash(rel)}"
    return f"{base}/{rel}"
