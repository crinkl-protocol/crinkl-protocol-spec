#!/usr/bin/env python3
"""Hostile tests for living public version claims."""
from __future__ import annotations

import copy
from pathlib import Path

import check_living_version_claims as checker


ROOT = Path(__file__).resolve().parents[1]


def rejected(name: str, documents: dict[str, str]) -> None:
    try:
        checker.validate_documents(documents)
    except ValueError:
        print(f"[living-version-claims-test] rejected: {name}")
        return
    raise AssertionError(f"{name}: mutation was accepted")


def main() -> int:
    checker.validate(ROOT)
    documents = checker.load_documents(ROOT)
    print("[living-version-claims-test] accepted: current documents")
    mutations = [
        ("V1 removed", "07-conformance/compatibility.md", "`SpendAttestationTokenV1`", "`RemovedTokenV1`"),
        ("V2 holder made mandatory", "07-conformance/compatibility.md", "is OPTIONAL; a V2 token without it remains valid", "is REQUIRED; a V2 token without it is invalid"),
        ("invented issuance default", "07-conformance/compatibility.md", "**no protocol-wide token issuance default**", "the protocol-wide token issuance default is V2"),
        ("rc.2 promoted", "07-conformance/compatibility.md", "not an observed public tag or public release.", "an observed public tag and public release."),
        ("rc.3 demoted", "07-conformance/compatibility.md", "are released immutable tags", "are unpublished release candidates"),
        ("rc.5 reviewed commit changed", "07-conformance/compatibility.md", checker.REVIEWED_COMMIT, "0" * 40),
        ("rc.5 reviewed tree changed", "07-conformance/compatibility.md", checker.REVIEWED_TREE, "0" * 40),
        ("later tree inherits review", "07-conformance/compatibility.md", "Later source, including this branch, is unassigned and cannot inherit that review.", "Later source inherits this review."),
        ("latest release wrong", "07-conformance/compatibility.md", "`v1.0.0-rc.4` is the latest released public package", "`v1.0.0-rc.3` is the latest released public package"),
        ("read-only overlap false rc.3 classification", "03-portability/spend-tokens-explainer.md", "\n", "\nv1.0.0-rc.3 is an unpublished release candidate.\n"),
    ]
    for name, path, old, new in mutations:
        altered = copy.deepcopy(documents)
        altered[path] = altered[path].replace(old, new, 1)
        rejected(name, altered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
