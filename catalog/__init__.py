"""Osteo-Fit CMF catalog - Flask application factory.

    flask --app catalog run --debug
    CATALOG_ASSET_BASE=static  -> relative asset URLs (used by tools/freeze.py)
"""
from __future__ import annotations

from pathlib import Path

from flask import Flask

from . import assets, views

PKG = Path(__file__).resolve().parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        ASSET_BASE="/static",
        MANIFEST_PATH=PKG / "static" / "img" / "manifest.json",
        CSV_PATH=Path(r"C:\workspace\Gssem_Solution\DB\16_OsteoFit CMF 품목.csv"),
        SEND_FILE_MAX_AGE_DEFAULT=60 * 60 * 24 * 365,
        COMPRESS_MIMETYPES=["text/html", "text/css", "application/javascript", "application/json"],
        JSON_AS_ASCII=False,
    )
    app.config.from_prefixed_env("CATALOG")
    if test_config:
        app.config.update(test_config)

    app.config["MANIFEST_PATH"] = Path(app.config["MANIFEST_PATH"])
    app.extensions["manifest"] = assets.load_manifest(app.config["MANIFEST_PATH"])
    app.jinja_env.globals.update(asset=assets.asset, manifest=assets.manifest)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    try:
        from flask_compress import Compress

        Compress(app)
    except ImportError:  # optional
        pass

    if app.debug:

        @app.before_request
        def _reload_manifest():
            p = app.config["MANIFEST_PATH"]
            cur = app.extensions["manifest"].get("_mtime_ns")
            if p.exists() and p.stat().st_mtime_ns != cur:
                app.extensions["manifest"] = assets.load_manifest(p)

    app.register_blueprint(views.bp)
    return app
