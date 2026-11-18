"""Small SVG builder for the Pain point schematics (nature-figure vector schematic style, web sizes).

One figure module builds the Korean and the English SVG from the same geometry, so the two pages
show the same picture. Text stays live <text>; no gradients, filters or scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

import functools
import os
import re

import material
from PIL import ImageFont

FONT_STACK = "Pretendard, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', Arial, sans-serif"
# Where Pretendard is looked for, in order: $PRETENDARD_DIR, then the usual macOS and Linux font
# folders (searched recursively, so ~/.local/share/fonts/pretendard/ works too).
_FONT_DIRS = [Path(p).expanduser() for p in (
    os.environ.get("PRETENDARD_DIR", ""), "~/Library/Fonts", "/Library/Fonts", "~/.local/share/fonts",
    "~/.fonts", "/usr/local/share/fonts", "/usr/share/fonts") if p]
# GitHub Octicons (MIT), shipped with mkdocs-material; see diagrams/figures/README.md.
ICON_DIR = Path(material.__file__).parent / "templates/.icons/octicons"

INK = "#1F2328"
MUTED_STROKE = "#9AA1AB"
GREY_FILL = "#F3F4F6"
CONTAINER = "#C3C8CF"
ACCENT = "#1F6FB2"
ACCENT_FILL = "#E8F1FA"
RED = "#C23B32"
RED_FILL = "#FBEAE8"

SIZE = 13        # ordinary text, px
SMALL = 12       # sub labels and edge labels
TITLE = 14       # panel titles (bold)


@functools.cache
def _font_path(name: str) -> Path:
    for folder in _FONT_DIRS:
        if (folder / name).is_file():
            return folder / name
        if folder.is_dir():
            found = next(folder.rglob(name), None)
            if found:
                return found
    raise FileNotFoundError(f"{name} not found in {', '.join(map(str, _FONT_DIRS))}; install Pretendard "
                            "or set PRETENDARD_DIR")


def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
    name = "Pretendard-SemiBold.otf" if bold else "Pretendard-Regular.otf"
    # BASIC layout (hinted integer advances) on every platform: with libraqm, Pillow measures some
    # labels a pixel wider, which shifts layouts and trips the fit checks.
    return ImageFont.truetype(str(_font_path(name)), size, layout_engine=ImageFont.Layout.BASIC)


def text_width(text: str, size: int = SIZE, bold: bool = False) -> float:
    # Measured with Pretendard; other fallback faces run a little wider, so callers keep slack.
    return _font(size, bold).getlength(text)


@dataclass
class Figure:
    width: int
    height: int
    parts: list[str] = field(default_factory=list)

    def rect(self, x, y, w, h, *, fill=GREY_FILL, stroke=MUTED_STROKE, width=1.2, dash=None, rx=6, gid=None):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        body = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="{width}"{dash_attr}/>')
        self.parts.append(f'<g id="{gid}">{body}</g>' if gid else body)

    def text(self, x, y, s, *, size=SIZE, bold=False, color=INK, anchor="middle"):
        weight = ' font-weight="600"' if bold else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}"{weight} fill="{color}" '
                          f'text-anchor="{anchor}">{escape(s)}</text>')

    def icon(self, name, x, y, size, color=INK):
        """Inline an Octicon (24px grid) with its top-left corner at (x, y)."""
        svg = (ICON_DIR / f"{name}-24.svg").read_text()
        inner = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", svg.strip())
        self.parts.append(f'<g transform="translate({x},{y}) scale({size / 24})" fill="{color}">{inner}</g>')

    def box(self, x, y, w, h, label, sub=None, *, icon=None, fill=GREY_FILL, stroke=MUTED_STROKE, color=INK, gid=None):
        """A component: name, optionally one short line on its job, optionally an icon.

        Tall boxes put the icon above the name; short boxes put it on the left."""
        self.rect(x, y, w, h, fill=fill, stroke=stroke, gid=gid)
        text_x, text_w, cy = x + w / 2, w, y + h / 2
        if icon and h >= 100:
            self.icon(icon, x + w / 2 - 14, cy - 50, 28, color)
            cy += 16
        elif icon:
            # Centre icon and text as one group so the icon never hugs the border.
            block = max(text_width(label), text_width(sub, SMALL) if sub else 0)
            start = x + (w - (20 + 10 + block)) / 2
            self.icon(icon, start, cy - 10, 20, color)
            text_x, text_w = start + 30 + block / 2, w - 30
            assert start - x >= 12, f"no room for icon padding in box {gid or label!r}: {start - x:.0f}px"
        if sub:
            self.text(text_x, cy - 3, label, color=color)
            self.text(text_x, cy + 14, sub, size=SMALL, color=color)
        else:
            self.text(text_x, cy + SIZE * 0.36, label, color=color)
        need = max(text_width(label), text_width(sub, SMALL) if sub else 0) + 16
        assert need <= text_w, f"label too wide for box {gid or label!r}: {need:.0f} > {text_w:.0f}"

    def stack(self, x, y, w, h, label, sub=None, *, mark="x8", **kw):
        """A repeated unit drawn once: two offset boxes and a xN mark."""
        self.rect(x + 6, y - 6, w, h, fill="#FFFFFF", stroke=MUTED_STROKE)
        self.box(x, y, w, h, label, sub, **kw)
        self.text(x + w + 4, y - 8, mark.replace("x", "×"), size=SMALL, anchor="start")

    def container(self, x, y, w, h, title, *, icon=None, stroke=CONTAINER, color=INK, bold=False):
        self.rect(x, y, w, h, fill="none", stroke=stroke, width=1.2, rx=8)
        tx = x + 10
        if icon:
            self.icon(icon, tx, y + 6, 15, color)
            tx += 20
        self.text(tx, y + 18, title, size=SMALL, bold=bold, color=color, anchor="start")

    def panel(self, x, y, letter, title):
        self.text(x, y, letter, size=TITLE + 2, bold=True, anchor="start")
        self.text(x + 18, y, title, size=TITLE, bold=True, anchor="start")

    def arrow(self, points, *, color=INK, width=1.6, dash=None, label=None, label_at=None, label_color=None):
        d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (px, py) in enumerate(points))
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        marker = {INK: "head-ink", RED: "head-red", ACCENT: "head-accent", MUTED_STROKE: "head-muted"}[color]
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash_attr} '
                          f'marker-end="url(#{marker})"/>')
        if label:
            lx, ly = label_at
            self.text(lx, ly, label, size=SMALL, color=label_color or INK)

    def line(self, points, *, color=INK, width=1.6, dash=None):
        d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (px, py) in enumerate(points))
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash_attr}/>')

    def block(self, x, y, *, color=RED, size=7):
        """A stop mark drawn as shapes (no glyph): a bar and a cross."""
        self.line([(x, y - 14), (x, y + 14)], color=color, width=2.4)
        self.line([(x + 6, y - size), (x + 6 + 2 * size, y + size)], color=color, width=2.2)
        self.line([(x + 6, y + size), (x + 6 + 2 * size, y - size)], color=color, width=2.2)

    def svg(self) -> str:
        markers = "".join(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
            for mid, col in (("head-ink", INK), ("head-red", RED), ("head-accent", ACCENT), ("head-muted", MUTED_STROKE))
        )
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}px" height="{self.height}px" '
                f'viewBox="0 0 {self.width} {self.height}" font-family="{FONT_STACK}">'
                f'<defs>{markers}</defs><rect width="100%" height="100%" fill="#FFFFFF"/>'
                + "".join(self.parts) + "</svg>\n")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.svg())
