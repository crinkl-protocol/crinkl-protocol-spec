#!/usr/bin/env python3
"""Fail closed when the public specification layout or local links drift."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "protocol/purpose",
    "protocol/core",
    "protocol/portability",
    "protocol/applications",
    "protocol/extensions",
    "conformance",
    "governance",
)
RETIRED = ("00-purpose", "06-extensions", "07-conformance", "08-governance")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_dir():
            errors.append(f"required directory missing: {relative}")
    for relative in RETIRED:
        if (ROOT / relative).exists():
            errors.append(f"retired numbered root exists: {relative}")

    for document in sorted(ROOT.rglob("*.md")):
        relative_document = document.relative_to(ROOT)
        if ".git" in relative_document.parts or relative_document.parts[:1] == ("versions",):
            continue
        text = document.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = match.group(1).split("#", 1)[0].split(' "', 1)[0]
            if not target or "://" in target or target.startswith(("#", "mailto:", "data:")):
                continue
            if not (document.parent / target).resolve().exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"broken local link: {relative_document}:{line}: {match.group(1)}")

    if errors:
        for error in errors:
            print(f"[repository-layout] {error}", file=sys.stderr)
        return 1
    print("[repository-layout] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
