#!/usr/bin/env python3
"""Render a ${VAR} template from environment variables and KEY=VALUE arguments.

Unlike envsubst, a missing variable is an error, so a typo never produces a manifest with an
empty image name or namespace. Write a literal dollar sign as $$.

A line of the form ``<indent>@@include path/relative/to/repo@@`` is replaced by that file,
indented to the same column and inserted verbatim (no ${VAR} substitution). This keeps shell
scripts readable as standalone files while embedding them in Kubernetes YAML.

    python3 scripts/render.py k8s/sandbox/deployment.yaml.tpl RUNTIME=gvisor | kubectl apply -f -
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from string import Template

REPO_ROOT = Path(__file__).resolve().parent.parent
INCLUDE = re.compile(r"^(?P<indent>[ \t]*)@@include (?P<path>\S+)@@[ \t]*$", re.MULTILINE)


def _expand_includes(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        indent = match.group("indent")
        body = (REPO_ROOT / match.group("path")).read_text().rstrip("\n")
        return "\n".join(indent + line if line else line for line in body.splitlines())

    return INCLUDE.sub(replace, text)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    template = Template(Path(argv[0]).read_text())
    values = dict(os.environ)
    for arg in argv[1:]:
        key, sep, value = arg.partition("=")
        if not sep:
            print(f"render: expected KEY=VALUE, got {arg!r}", file=sys.stderr)
            return 2
        values[key] = value
    try:
        rendered = template.substitute(values)
    except KeyError as exc:
        print(f"render: {argv[0]}: missing variable {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"render: {argv[0]}: {exc}", file=sys.stderr)
        return 1
    try:
        sys.stdout.write(_expand_includes(rendered))
    except OSError as exc:
        print(f"render: {argv[0]}: include failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
