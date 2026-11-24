# Schematic figures

The `figures_*.py` modules generate the diagrams used in the guide and the GitHub README.
Each module renders Korean (`<name>.ko.svg`) and English (`<name>.en.svg`) versions under
`docs/images/figures/`. That directory also contains diagrams maintained directly as SVGs.
MkDocs serves the matching file at `images/figures/<name>.svg` for each language.

```bash
# from the repository root, in the repository venv (Pillow, mkdocs-material)
python diagrams/figures/build.py --preview /tmp/figures   # previews need rsvg-convert
```

Style follows the vector schematic rules of the nature-figure skill, at web sizes: live text, one accent
colour (blue) for the sandbox or the fix, red only for the failure path, straight connectors, a `×N`
mark for repeated units. Every box, label and value comes from the page the figure belongs to.
Text is measured with Pretendard; keep some slack because readers' fallback fonts run wider.
`figlib.py` looks for `Pretendard-Regular.otf` and `Pretendard-SemiBold.otf` in `$PRETENDARD_DIR`, then in the
usual macOS and Linux font folders (`~/Library/Fonts`, `~/.local/share/fonts`, `/usr/share/fonts`, ...), and
measures with Pillow's BASIC layout on every platform so builds are byte-identical on macOS and Linux.

Icons are GitHub Octicons (MIT License, Copyright (c) GitHub Inc.), read from the copy that ships with
mkdocs-material (`material/templates/.icons/octicons/`).
