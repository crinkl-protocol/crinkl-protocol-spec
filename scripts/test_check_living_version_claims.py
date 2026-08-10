#!/usr/bin/env python3
"""Hostile tests for living public version claims."""
from __future__ import annotations

import copy
from pathlib import Path

import check_living_version_claims as checker


ROOT = Path(__file__).resolve().parents[1]


def rejected(name: str, documents: dict[str, str]) -> None:
    try:
        checker.validate_documents(documents, "RC8_SOURCE_CANDIDATE")
    except ValueError:
        print(f"[living-version-claims-test] rejected: {name}")
        return
    raise AssertionError(f"{name}: mutation was accepted")


def main() -> int:
    checker.validate(ROOT)
    documents = checker.load_documents(ROOT)
    print("[living-version-claims-test] accepted: current documents")

    if checker.read_json(ROOT / "versions/release.json").get("releaseVersion") != "1.0.0-rc.8":
        raise AssertionError("unexpected successor candidate version")
    print("[living-version-claims-test] accepted: rc.8 candidate uses rc.7 released wording; continuing hostile regressions")

    registry = checker.read_json(ROOT / "versions/release-registry.json")
    release = checker.read_json(ROOT / "versions/release.json")
    mutated_registry = copy.deepcopy(registry)
    mutated_registry["reviewedCandidateVersion"] = "1.0.0-rc.5"
    try:
        checker.validate(ROOT, documents, mutated_registry, release)
    except ValueError:
        print("[living-version-claims-test] rejected: rc.8 inherits historical reviewed candidate")
    else:
        raise AssertionError("rc.8 inherited historical reviewed candidate")

    mutated_release = copy.deepcopy(release)
    mutated_release["status"] = "RELEASED"
    try:
        checker.validate(ROOT, documents, registry, mutated_release)
    except ValueError:
        print("[living-version-claims-test] rejected: rc.8 candidate promoted to released")
    else:
        raise AssertionError("rc.8 candidate was promoted to released")

    altered_released = copy.deepcopy(documents)
    altered_released["conformance/compatibility.md"] = altered_released["conformance/compatibility.md"].replace(
        "`v1.0.0-rc.7` is the latest released public package",
        "`v1.0.0-rc.4` is the latest released public package",
        1,
    )
    try:
        checker.validate_documents(altered_released, "RC8_SOURCE_CANDIDATE")
    except ValueError:
        print("[living-version-claims-test] rejected: materialized release latest-version rollback")
    else:
        raise AssertionError("materialized release latest-version rollback was accepted")

    altered_released = copy.deepcopy(documents)
    altered_released["conformance/compatibility.md"] = altered_released["conformance/compatibility.md"].replace(
        "candidate profile maturity",
        "released profile maturity",
        1,
    )
    try:
        checker.validate_documents(altered_released, "RC8_SOURCE_CANDIDATE")
    except ValueError:
        print("[living-version-claims-test] rejected: materialized release candidate-profile promotion")
    else:
        raise AssertionError("materialized release candidate-profile promotion was accepted")
    mutations = [
        ("V1 removed", "conformance/compatibility.md", "`SpendAttestationTokenV1`", "`RemovedTokenV1`"),
        ("V2 holder made mandatory", "conformance/compatibility.md", "is OPTIONAL; a V2 token without it remains valid", "is REQUIRED; a V2 token without it is invalid"),
        ("invented issuance default", "conformance/compatibility.md", "**no protocol-wide token issuance default**", "the protocol-wide token issuance default is V2"),
        ("rc.2 promoted", "conformance/compatibility.md", "not an observed public tag or public release.", "an observed public tag and public release."),
        ("rc.3 demoted", "conformance/compatibility.md", "are released immutable tags", "are unpublished release candidates"),
        ("rc.1 omitted", "conformance/compatibility.md", "`v1.0.0-rc.1`, ", ""),
        ("rc.1 demoted", "conformance/compatibility.md", "`v1.0.0-rc.1`, `v1.0.0-rc.3`, and `v1.0.0-rc.4` are released immutable tags", "`v1.0.0-rc.1` is an unpublished candidate"),
        ("rc.5 reviewed commit changed", "conformance/compatibility.md", checker.REVIEWED_COMMIT, "0" * 40),
        ("rc.5 reviewed tree changed", "conformance/compatibility.md", checker.REVIEWED_TREE, "0" * 40),
        ("later tree inherits review", "conformance/compatibility.md", "Any later tree remains unassigned unless a new exact candidate identity and independent review record it.", "Any later tree inherits this review."),
        ("latest release wrong", "conformance/compatibility.md", "`v1.0.0-rc.7` is the latest released public package", "`v1.0.0-rc.3` is the latest released public package"),
        ("read-only overlap false rc.3 classification", "protocol/portability/spend-tokens-explainer.md", "\n", "\nv1.0.0-rc.3 is an unpublished release candidate.\n"),
    ]
    for name, path, old, new in mutations:
        altered = copy.deepcopy(documents)
        altered[path] = altered[path].replace(old, new, 1)
        rejected(name, altered)
    altered = copy.deepcopy(documents)
    altered["README.md"] = altered["README.md"].replace(
        "**v1.0.0-rc.5** historical exact reviewed source candidate — not published.",
        "**v1.0.0-rc.5** current source candidate — not published.",
        1,
    )
    rejected("rc.5 historical classification removed", altered)
    altered = copy.deepcopy(documents)
    altered["governance/versioning.md"] = altered["governance/versioning.md"].replace(
        "Historical exact reviewed source candidate: **1.0.0-rc.5** (`REVIEWED_CANDIDATE_NOT_PUBLISHED`)",
        "Current public repository source candidate: **1.0.0-rc.5** (`REVIEWED_CANDIDATE_NOT_PUBLISHED`)",
        1,
    )
    rejected("rc.5 promoted to current", altered)
    altered = copy.deepcopy(documents)
    expected_rc8_versioning = (
        "`v1.0.0-rc.7` is the latest released public package. Current public repository\n"
        "source candidate: **1.0.0-rc.8** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),\n"
        "conformance suite 5; it is unreviewed, unpublished, not publishable, and does\n"
        "not inherit rc.5 review."
    )
    if expected_rc8_versioning not in altered["governance/versioning.md"]:
        raise AssertionError("rc.8 versioning source-candidate fixture missing")
    altered["governance/versioning.md"] = altered["governance/versioning.md"].replace(
        "not publishable, and does\nnot inherit rc.5 review.",
        "publishable and inherits rc.5 review.",
        1,
    )
    rejected("rc.8 versioning candidate becomes publishable or inherits rc.5 review", altered)
    altered = copy.deepcopy(documents)
    altered["conformance/compatibility.md"] = altered["conformance/compatibility.md"].replace(
        "preserves historical rc.5 review boundaries", "inherits rc.5 review", 1
    )
    rejected("rc.7 inherits rc.5 review", altered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
