#!/usr/bin/env python3
"""Focused regression checks for the change-boundary classifier."""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import check_change_boundary as checker


CAMPAIGN_MATURITY_PAGES = (
    "protocol/applications/campaigns/README.md",
    "protocol/applications/campaigns/campaign-template-catalog.md",
    "protocol/applications/campaigns/solana-proof-verification.md",
)


def boundary_record(excluded_field: str | None = None) -> str:
    lines = [
        f"- **{field}:** Concrete {field.lower()} classification for this campaign maturity change."
        for field in checker.FIELDS
        if field != excluded_field
    ]
    return "\n".join(
        [
            *lines,
            "",
            "- [x] I classified the change using the protocol/business and onchain/offchain tests.",
            "- [x] I did not describe draft, experimental, or unpublished behavior as adopted protocol behavior.",
        ]
    )


def run_check(path: str, body: str) -> int:
    with tempfile.TemporaryDirectory() as directory:
        body_file = Path(directory) / "body.md"
        body_file.write_text(body, encoding="utf-8")
        argv = sys.argv
        try:
            sys.argv = [
                "check_change_boundary.py",
                "--changed-file",
                path,
                "--body-file",
                str(body_file),
            ]
            with contextlib.redirect_stderr(io.StringIO()):
                return checker.main()
        finally:
            sys.argv = argv


def main() -> int:
    complete_record = boundary_record()
    for path in CAMPAIGN_MATURITY_PAGES:
        if run_check(path, complete_record) != 0:
            raise AssertionError(f"complete record rejected for {path}")
    print("[change-boundary-test] accepted: campaign maturity pages with six fields")

    for field in checker.FIELDS:
        if run_check(CAMPAIGN_MATURITY_PAGES[0], boundary_record(field)) == 0:
            raise AssertionError(f"campaign maturity page accepted without {field}")
    print("[change-boundary-test] rejected: each missing boundary field")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
