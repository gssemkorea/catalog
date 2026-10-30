from __future__ import annotations

from flask import Blueprint, abort, jsonify, redirect, render_template, request

from .assets import asset, manifest

bp = Blueprint("catalog", __name__)


def cat_payload() -> dict:
    """The small key -> URL map the page script needs for the zoom modal."""
    p = {}
    for key, e in manifest().get("products", {}).items():
        p[key] = {
            "m": asset(e["m"]),
            "mw": e.get("mw"),
            "f": asset(e["f"]),
            "fw": e.get("fw"),
            "w": e["w"],
            "h": e["h"],
        }
    return {"p": p}


@bp.get("/")
def index():
    return render_template("catalog.html", cat=cat_payload())


@bp.get("/3d")
def sample3d():
    """Sample page for the interactive 3D viewer (model-viewer + Draco GLB)."""
    return render_template("sample3d.html")


@bp.get("/img/<key>")
def img(key: str):
    e = manifest().get("products", {}).get(key)
    if not e:
        abort(404)
    v = request.args.get("v", "m")
    if v not in ("t", "m", "f"):
        abort(400)
    return redirect(asset(e[v]), code=302)


@bp.get("/favicon.ico")
def favicon():
    return "", 204


@bp.get("/healthz")
def healthz():
    m = manifest()
    return jsonify(ok=True, products=len(m.get("products", {})), built=m.get("built"))
