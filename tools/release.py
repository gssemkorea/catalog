"""build --check -> pytest -> freeze -> inline, in one go.

    python tools/release.py [--public] [--skip-tests]

--public refuses to continue while any banner source is license=unverified.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import config  # noqa: E402

PY = sys.executable


def run(*cmd: str) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=config.ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()

    run(PY, "tools/build_assets.py")
    man = json.loads(config.MANIFEST.read_text(encoding="utf-8"))
    if args.public and man.get("license_unverified"):
        print(f"ABORT: {man['license_unverified']} banner source(s) have license=unverified "
              f"(see {config.REPORT}). Fix assets_src/banners.json before a public release.")
        return 2
    if not args.skip_tests:
        run(PY, "-m", "pytest", "-q")
    run(PY, "tools/freeze.py")
    run(PY, "tools/inline.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
