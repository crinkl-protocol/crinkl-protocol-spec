#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


RELEVANT_PREFIXES = (
    "00-purpose/",
    "protocol/core/",
    "protocol/core/",
    "protocol/portability/",
    "protocol/applications/conditions/",
    "protocol/applications/economics/",
    "06-extensions/",
    "07-conformance/",
    "08-governance/",
    "bindings/",
    "formal/",
    "schemas/",
)

RELEVANT_FILES = {
    "README.md",
    "versions/CHANGELOG.md",
}

FIELDS = (
    "Business policy",
    "Protocol artifacts",
    "Offchain state and computation",
    "Onchain commitment or execution",
    "Verification and disputes",
    "Maturity and adoption",
)

AFFIRMATIONS = (
    "I classified the change using the protocol/business and onchain/offchain tests.",
    "I did not describe draft, experimental, or unpublished behavior as adopted protocol behavior.",
)

PLACEHOLDER = re.compile(r"^(?:n/?a|none|tbd|todo|unknown|pending|-)\.?$", re.IGNORECASE)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Require a protocol/business/onchain boundary record for spec changes."
    )
    parser.add_argument("--base", help="Base git revision used to discover changed files")
    parser.add_argument("--head", help="Head git revision used to discover changed files")
    parser.add_argument("--body-file", type=Path, help="Read the pull-request body from this file")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed path; repeat to bypass git diff discovery",
    )
    return parser.parse_args()


def changed_files(args: argparse.Namespace) -> list[str]:
    if args.changed_file:
        return args.changed_file
    if not args.base or not args.head:
        raise ValueError("provide --changed-file or both --base and --head")
    result = subprocess.run(
        ["git", "diff", "--name-only", args.base, args.head, "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_relevant(path: str) -> bool:
    return path in RELEVANT_FILES or path.startswith(RELEVANT_PREFIXES)


def body_text(args: argparse.Namespace) -> str:
    if args.body_file:
        return args.body_file.read_text(encoding="utf-8")
    return os.environ.get("PR_BODY", "")


def field_value(body: str, field: str) -> str | None:
    pattern = re.compile(
        rf"(?mi)^[ \t]*-[ \t]*\*\*{re.escape(field)}:\*\*[ \t]*(.*?)[ \t]*$"
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else None


def main() -> int:
    args = parse_args()
    try:
        changed = changed_files(args)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"[boundary-check] unable to discover changed files: {exc}", file=sys.stderr)
        return 2

    relevant = sorted(path for path in changed if is_relevant(path))
    if not relevant:
        print("[boundary-check] SKIP (no spec or requirements surfaces changed)")
        return 0

    body = HTML_COMMENT.sub("", body_text(args))
    errors: list[str] = []

    for field in FIELDS:
        value = field_value(body, field)
        if value is None:
            errors.append(f"missing Boundary impact field: {field}")
        elif len(value) < 12 or PLACEHOLDER.fullmatch(value):
            errors.append(f"Boundary impact field needs a concrete answer: {field}")

    for affirmation in AFFIRMATIONS:
        checked = re.search(
            rf"(?mi)^\s*-\s*\[[xX]\]\s*{re.escape(affirmation)}\s*$", body
        )
        if not checked:
            errors.append(f"required affirmation is not checked: {affirmation}")

    if errors:
        print("[boundary-check] FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("Relevant changed paths:", file=sys.stderr)
        for path in relevant[:20]:
            print(f"- {path}", file=sys.stderr)
        return 1

    print(
        f"[boundary-check] OK ({len(relevant)} spec/requirements path(s) classified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
