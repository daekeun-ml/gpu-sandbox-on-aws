"""Build every schematic into docs/images/figures/<name>.<lang>.svg.

Every figures_*.py module next to this file exports FIGURES = {name: draw(lang) -> Figure}.
usage: python3 diagrams/figures/build.py [--only PREFIX] [--preview DIR]   (previews need rsvg-convert)
Needs Pillow and the Pretendard font (text measuring only).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import importlib  # noqa: E402

OUT = HERE.parents[1] / "docs/images/figures"


def load_figures() -> dict:
    figures = {}
    for module_path in sorted(HERE.glob("figures_*.py")):
        module = importlib.import_module(module_path.stem)
        clash = figures.keys() & module.FIGURES.keys()
        if clash:
            raise SystemExit(f"duplicate figure names in {module_path.name}: {sorted(clash)}")
        figures.update(module.FIGURES)
    return figures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path, help="also render PNG previews into this directory")
    parser.add_argument("--only", default="", help="build only figures whose name starts with this prefix")
    args = parser.parse_args()
    for name, draw in load_figures().items():
        if not name.startswith(args.only):
            continue
        for lang in ("ko", "en"):
            path = OUT / f"{name}.{lang}.svg"
            draw(lang).save(path)
            print(f"wrote {path.relative_to(HERE.parents[1])}")
            if args.preview:
                if not shutil.which("rsvg-convert"):
                    raise SystemExit("rsvg-convert not found (brew install librsvg)")
                args.preview.mkdir(parents=True, exist_ok=True)
                subprocess.run(["rsvg-convert", "-z", "2", "-o", str(args.preview / f"{name}.{lang}.png"), str(path)],
                               check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
