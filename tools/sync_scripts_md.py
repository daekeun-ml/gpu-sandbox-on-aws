#!/usr/bin/env python3
"""Build SCRIPTS.md and SCRIPTS.en.md (repository root, read on GitHub) from the guidebook's
script reference (docs/reference/scripts.md and scripts.en.md).

    python3 tools/sync_scripts_md.py          # write both files
    python3 tools/sync_scripts_md.py --check  # exit 1 if they are out of date (CI)

Edit the guidebook page, then run this. The conversion turns the MkDocs TL;DR box into a GitHub
note and relative guidebook links into absolute links to the published site.
"""
from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://daekeun-ml.github.io/gpu-sandbox-on-aws/"
PAGES = {
    # target: (source, site prefix, language switch line)
    "SCRIPTS.md": ("docs/reference/scripts.md", SITE, "**한국어** | [English](SCRIPTS.en.md)"),
    "SCRIPTS.en.md": ("docs/reference/scripts.en.md", SITE + "en/", "[한국어](SCRIPTS.md) | **English**"),
}
HEADER = {
    "SCRIPTS.md": "이 파일은 가이드북의 [스크립트 레퍼런스]({site}reference/scripts/)에서 만듭니다"
                  "(`tools/sync_scripts_md.py`). 고칠 때는 `docs/reference/scripts.md`를 고치세요.",
    "SCRIPTS.en.md": "This file is built from the guidebook's [Script reference]({site}reference/scripts/)"
                     " (`tools/sync_scripts_md.py`). To change it, edit `docs/reference/scripts.en.md`.",
}
LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(((?!https?://|#|mailto:)[^)\s]+)\)")
IMAGE = re.compile(r"!\[([^\]]*)\]\(((?!https?://)[^)\s]+)\)")


def repo_image(target: str, lang: str) -> str:
    """Guidebook image path (relative to docs/reference/) -> repository path GitHub can show.
    The i18n plugin serves name.svg from name.ko.svg or name.en.svg; GitHub needs the real file."""
    path = posixpath.normpath(posixpath.join("docs/reference", target))
    if not (ROOT / path).exists():
        stem, dot, ext = path.rpartition(".")
        for candidate in (f"{stem}.{lang}.{ext}", f"{stem}.ko.{ext}"):
            if (ROOT / candidate).exists():
                return candidate
    return path


def site_url(target: str, prefix: str) -> str:
    path, _, anchor = target.partition("#")
    resolved = posixpath.normpath(posixpath.join("reference", path))
    if resolved.endswith(".md"):
        resolved = resolved[: -len(".md")]
    if resolved.endswith("/index") or resolved == "index":
        resolved = resolved[: -len("index")]
    url = prefix + (resolved.rstrip("/") + "/" if resolved else "")
    return url + ("#" + anchor if anchor else "")


def convert(target: str) -> str:
    source, prefix, switch = PAGES[target]
    text = (ROOT / source).read_text()
    # !!! info "TL;DR"\n    body  ->  > [!NOTE]\n> **TL;DR** body
    text = re.sub(r'^!!! info "TL;DR"\n((?:    .*\n?)+)',
                  lambda m: "> [!NOTE]\n> **TL;DR** " + " ".join(l.strip() for l in m.group(1).splitlines()) + "\n",
                  text, count=1, flags=re.M)
    # GitHub does not interpret MkDocs heading attributes.
    text = re.sub(r"^(#{1,6} .*?) \{ #([\w-]+) \}$",
                  r'<a name="\2"></a>\n\n\1', text, flags=re.M)
    lang = "en" if target.endswith(".en.md") else "ko"
    text = IMAGE.sub(lambda m: f"![{m.group(1)}](" + repo_image(m.group(2), lang) + ")", text)
    text = LINK.sub(lambda m: f"[{m.group(1)}](" + site_url(m.group(2), prefix) + ")", text)
    title, _, rest = text.partition("\n")
    note = HEADER[target].format(site=prefix)
    return f"{switch}\n\n{title}\n\n{note}\n{rest}"


def main() -> int:
    check = "--check" in sys.argv[1:]
    stale = []
    for target in PAGES:
        want = convert(target)
        path = ROOT / target
        if check:
            if not path.exists() or path.read_text() != want:
                stale.append(target)
        else:
            path.write_text(want)
            print(f"wrote {target}")
    if stale:
        print(f"out of date: {', '.join(stale)}; run python3 tools/sync_scripts_md.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
