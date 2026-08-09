#!/usr/bin/env python3
"""Fail closed on living public compatibility and release-state claims."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "versions/release-registry.json"
FINALIZATION = "versions/v1.0.0-rc.5/finalization.json"
REVIEWED_COMMIT = "81237937833ab32e5ce92d3b5ceed72854baecef"
REVIEWED_TREE = "9121bdfbfc428f73557e993f1bd6e295ba733a12"
SCOPE = (
    "The following preserved\nrc.5 transition text applies only to public-spec commit\n"
    f"`{REVIEWED_COMMIT}` / tree\n`{REVIEWED_TREE}`:"
)
LATER_TREE = (
    "It does not classify any later tree; any later tree remains unassigned unless a\n"
    "new exact candidate identity and independent review record it."
)
LIVING_PATHS = (
    "README.md", "SECURITY.md", "03-portability/spend-attestation-token.md",
    "06-extensions/campaign-experiment-profile.md", "06-extensions/merchant-authority.md",
    "07-conformance/compatibility.md", "07-conformance/vectors.md",
    "07-conformance/verifier-test-suite.md",
    "07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md",
    "08-governance/glossary.md", "08-governance/protocol-v1-index.md",
    "08-governance/versioning.md", "08-governance/zk-beta-release-checklist.md",
    "versions/CHANGELOG.md",
)
READ_ONLY_OVERLAP = (
    "03-portability/spend-tokens-explainer.md",
    "04-condition-layer/campaign-commitment.md",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path}: JSON root must be an object")
    return value


def load_documents(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for rel in (*LIVING_PATHS, *READ_ONLY_OVERLAP):
        try:
            result[rel] = (root / rel).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read living document {rel}: {exc}") from exc
    return result


def validate_registry(registry: dict[str, Any]) -> None:
    releases = registry.get("releases")
    require(isinstance(releases, dict), "release registry releases missing")
    require(registry.get("latestReleasedVersion") == "1.0.0-rc.4", "latest released version drift")
    require(registry.get("reviewedCandidateVersion") == "1.0.0-rc.5", "reviewed candidate version drift")
    for version in ("1.0.0-rc.1", "1.0.0-rc.3", "1.0.0-rc.4"):
        require(isinstance(releases.get(version), dict) and releases[version].get("status") == "RELEASED", f"{version} must be released")
    candidate = releases.get("1.0.0-rc.5")
    require(isinstance(candidate, dict) and candidate.get("status") == "REVIEWED_CANDIDATE_NOT_PUBLISHED", "rc.5 candidate state drift")
    source = candidate.get("source")
    require(isinstance(source, dict) and source.get("commit") == REVIEWED_COMMIT and source.get("tree") == REVIEWED_TREE, "rc.5 reviewed commit/tree drift")
    observed = registry.get("embeddedWireVersionObservations", {}).get("1.0.0-rc.2", {})
    require(observed.get("classification") == "EMBEDDED_WIRE_LABEL_NOT_A_PUBLIC_RELEASE_CLASSIFICATION_PENDING", "rc.2 public-release classification drift")


def validate_documents(documents: dict[str, str]) -> None:
    compatibility = documents["07-conformance/compatibility.md"]
    for marker in (
        "`v1.0.0-rc.1`, `v1.0.0-rc.3`, and `v1.0.0-rc.4` are released immutable tags",
        "`v1.0.0-rc.4` is the latest released public package",
        REVIEWED_COMMIT, REVIEWED_TREE, "Any later tree remains unassigned unless a new exact candidate identity and independent review record it.",
        "`1.0.0-rc.2` is not an observed public tag or public release.",
        "`SpendAttestationTokenV1` and `SpendAttestationTokenV2` remain valid supported sibling schemas.",
        "V2 `holderBinding` is OPTIONAL; a V2 token without it remains valid",
        "**no protocol-wide token issuance default**",
    ):
        require(marker in compatibility, f"compatibility record missing: {marker}")
    require(not re.search(r"\bN(?:-1|\+1)?\b", compatibility), "generic adjacent-version compatibility heuristic remains")
    require("including this branch" not in compatibility, "branch-relative compatibility wording remains")
    required = {
        "README.md": ("## Release and source state", "`v1.0.0-rc.4` is the latest released public package.", "**v1.0.0-rc.5** release candidate source — not yet published.", "P4.4 and P9 remain blockers."),
        "SECURITY.md": (REVIEWED_COMMIT, REVIEWED_TREE, "later source is unassigned"),
        "03-portability/spend-attestation-token.md": ("SpendAttestationTokenV1` and `SpendAttestationTokenV2` are both supported", "no protocol-wide token issuance default"),
        "06-extensions/campaign-experiment-profile.md": ("supported embedded wire/source/binding history, not an observed public tag or public release",),
        "06-extensions/merchant-authority.md": ("supported embedded wire/source/binding history", "not an\nobserved public tag or public release classification"),
        "07-conformance/vectors.md": ("included in released `v1.0.0-rc.3` / suite 2",),
        "07-conformance/verifier-test-suite.md": ("The rc.5 candidate\nintentionally fails that gate until P4.4/P9 complete the governed release.", REVIEWED_COMMIT, "later source is unassigned"),
        "07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md": ("This is a source-only candidate bundle", REVIEWED_COMMIT, "later source is unassigned"),
        "08-governance/glossary.md": ("V2 `holderBinding` is\nOPTIONAL, so a V2 token without it remains valid",),
        "08-governance/protocol-v1-index.md": ("released `v1.0.0-rc.3` / conformance suite 2", REVIEWED_COMMIT),
        "08-governance/versioning.md": ("`v1.0.0-rc.4` is the latest released public package.", "Current public repository source candidate: **1.0.0-rc.5** (`RELEASE_CANDIDATE_NOT_PUBLISHED`)", "`v1.0.0-rc.3` and `v1.0.0-rc.4` are released public packages; rc.4 is the\nlatest released package."),
        "08-governance/zk-beta-release-checklist.md": ("embedded wire/source/binding history label, not an observed\npublic tag or public-release classification",),
        "versions/CHANGELOG.md": ("`v1.0.0-rc.4` is the latest released public package.", "The current public repository release candidate is **v1.0.0-rc.5**, an\nunpublished SemVer prerelease.", "## v1.0.0-rc.5 release candidate (not published)", "does not promote the W3C profile beyond candidate maturity."),
    }
    for rel, markers in required.items():
        for marker in markers:
            require(marker in documents[rel], f"{rel}: required living wording missing: {marker}")
    for rel, legacy_markers in {
        "README.md": ("**v1.0.0-rc.5** release candidate source — not yet published.", "This is an unpublished SemVer prerelease candidate, not a stable `v1.0.0`", "P4.4 and P9 remain blockers."),
        "08-governance/versioning.md": ("Current public repository source candidate: **1.0.0-rc.5** (`RELEASE_CANDIDATE_NOT_PUBLISHED`)", "unpublished SemVer prerelease candidate"),
        "versions/CHANGELOG.md": ("The current public repository release candidate is **v1.0.0-rc.5**, an\nunpublished SemVer prerelease.", "## v1.0.0-rc.5 release candidate (not published)"),
    }.items():
        text = documents[rel]
        scope_at = text.find(SCOPE)
        require(scope_at >= 0, f"{rel}: exact rc.5 scope qualification missing")
        for marker in legacy_markers:
            marker_at = text.find(marker)
            require(marker_at >= 0 and text.count(marker) == 1, f"{rel}: legacy rc.5 marker must occur exactly once: {marker}")
            require(scope_at < marker_at, f"{rel}: rc.5 scope qualification must precede legacy marker: {marker}")
        require(text.find(LATER_TREE) > max(text.find(marker) for marker in legacy_markers), f"{rel}: later-tree noninheritance qualification must follow legacy markers")
    corpus = "\n".join(documents.values())
    for pattern in (
        r"(?i)unpublished\s+`?v?1\.0\.0-rc\.3`?",
        r"(?i)v1\.0\.0-rc\.3[^\n]{0,90}(?:release candidate|not published)",
        r"(?i)v1\.0\.0-rc\.4[^\n]{0,90}(?:unpublished|release candidate)",
        r"(?i)protocol-wide token issuance default is(?:\s+)?v2",
        r"including this branch",
    ):
        require(not re.search(pattern, corpus), f"false living release/issuance classification: {pattern}")


def validate_finalization_markers(root: Path) -> None:
    plan = read_json(root / FINALIZATION)
    transitions = plan.get("documentationTransitions")
    require(isinstance(transitions, list), "finalization documentation transitions missing")
    for transition in transitions:
        require(isinstance(transition, dict), "finalization transition shape drift")
        path, candidate = transition.get("path"), transition.get("candidateMarker")
        require(isinstance(path, str) and isinstance(candidate, str), "finalization candidate marker shape drift")
        try:
            text = (root / path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read finalization documentation path {path}: {exc}") from exc
        require(candidate in text, f"finalization candidate marker missing: {path}: {candidate}")


def validate(root: Path, documents: dict[str, str] | None = None) -> None:
    validate_registry(read_json(root / REGISTRY))
    validate_documents(load_documents(root) if documents is None else documents)
    validate_finalization_markers(root)


def main() -> int:
    try:
        validate(ROOT)
    except ValueError as exc:
        print(f"[living-version-claims] {exc}", file=sys.stderr)
        return 1
    print("[living-version-claims] OK (exact release state, compatibility, and rc.5 review scope)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
