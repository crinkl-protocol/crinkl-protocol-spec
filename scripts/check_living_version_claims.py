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
REVIEWED_COMMIT = "81237937833ab32e5ce92d3b5ceed72854baecef"
REVIEWED_TREE = "9121bdfbfc428f73557e993f1bd6e295ba733a12"
LIVING_PATHS = (
    "README.md", "SECURITY.md", "protocol/portability/spend-attestation-token.md",
    "06-extensions/campaign-experiment-profile.md", "06-extensions/merchant-authority.md",
    "07-conformance/compatibility.md", "07-conformance/vectors.md", "07-conformance/vectors/v1/README.md",
    "07-conformance/verifier-test-suite.md",
    "07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md",
    "08-governance/glossary.md", "08-governance/protocol-v1-index.md",
    "08-governance/versioning.md", "08-governance/zk-beta-release-checklist.md",
    "versions/CHANGELOG.md",
)
READ_ONLY_OVERLAP = (
    "protocol/portability/spend-tokens-explainer.md",
    "protocol/applications/conditions/campaign-commitment.md",
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


def validate_registry(registry: dict[str, Any], release_manifest: dict[str, Any]) -> None:
    releases = registry.get("releases")
    require(isinstance(releases, dict), "release registry releases missing")
    for version in ("1.0.0-rc.1", "1.0.0-rc.3", "1.0.0-rc.4"):
        require(isinstance(releases.get(version), dict) and releases[version].get("status") == "RELEASED", f"{version} must be released")
    candidate = releases.get("1.0.0-rc.5")
    require(isinstance(candidate, dict) and candidate.get("status") == "REVIEWED_CANDIDATE_NOT_PUBLISHED", "rc.5 candidate state drift")
    source = candidate.get("source")
    require(isinstance(source, dict) and source.get("commit") == REVIEWED_COMMIT and source.get("tree") == REVIEWED_TREE, "rc.5 reviewed commit/tree drift")
    observed = registry.get("embeddedWireVersionObservations", {}).get("1.0.0-rc.2", {})
    require(observed.get("classification") == "EMBEDDED_WIRE_LABEL_NOT_A_PUBLIC_RELEASE_CLASSIFICATION_PENDING", "rc.2 public-release classification drift")
    if release_manifest.get("status") == "RELEASE_CANDIDATE_NOT_PUBLISHED":
        require(release_manifest.get("releaseVersion") == "1.0.0-rc.8", "rc.8 source candidate version drift")
        require(release_manifest.get("requiredTag") == "v1.0.0-rc.8", "rc.8 source candidate tag drift")
        require(release_manifest.get("conformance", {}).get("suiteVersion") == 5, "rc.8 source candidate suite drift")
        require(registry.get("latestReleasedVersion") == "1.0.0-rc.7", "rc.8 candidate latest released version drift")
        require(registry.get("candidateState") == "SOURCE_CANDIDATE_AWAITING_REVIEW_NOT_PUBLISHABLE", "rc.8 candidate state drift")
        require(registry.get("reviewedCandidateVersion") is None, "unreviewed rc.8 source candidate must not set reviewedCandidateVersion")
        released = releases.get("1.0.0-rc.7")
        require(isinstance(released, dict) and released.get("status") == "RELEASED", "rc.7 released registry entry missing")
    elif release_manifest.get("status") == "RELEASED":
        require(release_manifest.get("releaseVersion") == "1.0.0-rc.7", "current public package version drift")
        require(release_manifest.get("requiredTag") == "v1.0.0-rc.7", "current public package tag drift")
        require(release_manifest.get("conformance", {}).get("suiteVersion") == 4, "current public package suite drift")
        released = releases.get("1.0.0-rc.7")
        require(registry.get("latestReleasedVersion") == "1.0.0-rc.7", "released latest version drift")
        require(registry.get("candidateState") == "NO_ACTIVE_OR_PUBLISHABLE_CANDIDATE", "released candidate state drift")
        require(registry.get("reviewedCandidateVersion") == "1.0.0-rc.5", "released package reviewed candidate pointer drift")
        require(isinstance(released, dict) and released.get("status") == "RELEASED", "rc.7 released registry entry missing")
        require(released.get("previousRelease") == "1.0.0-rc.4", "rc.7 released predecessor drift")
        require(released.get("source", {}).get("tagTarget", {}).get("tag") == "v1.0.0-rc.7", "rc.7 tag-target authority drift")
    else:
        raise ValueError("current public package status is neither candidate nor released")


def validate_documents(documents: dict[str, str], release_status: str = "RELEASE_CANDIDATE_NOT_PUBLISHED") -> None:
    compatibility = documents["07-conformance/compatibility.md"]
    for marker in (
        "`v1.0.0-rc.1`, `v1.0.0-rc.3`, and `v1.0.0-rc.4` are released immutable tags",
        REVIEWED_COMMIT, REVIEWED_TREE, "Any later tree remains unassigned unless a new exact candidate identity and independent review record it.",
        "`1.0.0-rc.2` is not an observed public tag or public release.",
        "`SpendAttestationTokenV1` and `SpendAttestationTokenV2` remain valid supported sibling schemas.",
        "V2 `holderBinding` is OPTIONAL; a V2 token without it remains valid",
        "**no protocol-wide token issuance default**",
    ):
        require(marker in compatibility, f"compatibility record missing: {marker}")
    release_markers = {
        "RELEASE_CANDIDATE_NOT_PUBLISHED": {
            "latest": "`v1.0.0-rc.4` is the latest released public package",
            "compatibility": "| `v1.0.0-rc.7` source candidate | Current suite-4 source candidate; unreviewed, unpublished, and not publishable. | It does not inherit the rc.5 review and requires a new exact candidate identity and independent review. |",
            "README.md": "`v1.0.0-rc.4` is the latest released public package. Current public repository\nsource candidate: **v1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),\nconformance suite 4; it is unreviewed, unpublished, not publishable, and does\nnot inherit rc.5 review.",
            "SECURITY.md": "- `v1.0.0-rc.7` is the current unreviewed source candidate and conformance\n  suite 4 (`RELEASE_CANDIDATE_NOT_PUBLISHED`); it is unpublished and not\n  publishable until separately reviewed.",
            "08-governance/versioning.md": "`v1.0.0-rc.4` is the latest released public package. Current public repository source candidate: **1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`), conformance suite 4; it is unreviewed, unpublished, not publishable, and does not inherit rc.5 review.",
            "versions/CHANGELOG.md": "`v1.0.0-rc.4` is the latest released public package. Current public repository\nsource candidate: **1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),\nconformance suite 4; it is unreviewed, unpublished, not publishable, and does\nnot inherit rc.5 review.",
            "07-conformance/verifier-test-suite.md": "status: release-candidate",
            "07-conformance/vectors/v1/README.md": "status: release-candidate",
        },
        "RELEASED": {
            "latest": "`v1.0.0-rc.7` is the latest released public package",
            "compatibility": "| `v1.0.0-rc.7` public release | Latest released suite-4 public package. | It preserves historical rc.5 review boundaries, candidate profile maturity, and separate runtime/production governance. |",
            "README.md": "`v1.0.0-rc.7` is the latest released public package. Current public repository\nrelease: **v1.0.0-rc.7** (`RELEASED`), conformance suite 4; it preserves the\nexplicit rc.1/rc.2 wire support set and remains independent from runtime,\nvalidator, authority, and production activation.",
            "SECURITY.md": "- `v1.0.0-rc.7` is the released public package and conformance suite 4;\n  release status does not activate runtime, validator, authority, or\n  production behavior.",
            "08-governance/versioning.md": "`v1.0.0-rc.7` is the latest released public package. Current public repository release: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote candidate profiles or activate runtime, validator, authority, or production behavior.",
            "versions/CHANGELOG.md": "`v1.0.0-rc.7` is the latest released public package. Current public repository\nrelease: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote\ncandidate profiles or activate runtime, validator, authority, deployment, or\nproduction behavior.",
            "07-conformance/verifier-test-suite.md": "status: released",
            "07-conformance/vectors/v1/README.md": "status: released",
        },
        "RC8_SOURCE_CANDIDATE": {
            "latest": "`v1.0.0-rc.7` is the latest released public package",
            "compatibility": "| `v1.0.0-rc.7` public release | Latest released suite-4 public package. | It preserves historical rc.5 review boundaries, candidate profile maturity, and separate runtime/production governance. |",
            "README.md": "`v1.0.0-rc.7` is the latest released public package. Current public repository\nsource candidate: **v1.0.0-rc.8** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),\nconformance suite 5; it is unreviewed, unpublished, not publishable, and does\nnot inherit rc.5 review.",
            "SECURITY.md": "- `v1.0.0-rc.7` is the released public package and conformance suite 4;\n  release status does not activate runtime, validator, authority, or\n  production behavior.",
            "08-governance/versioning.md": "`v1.0.0-rc.7` is the latest released public package. Current public repository release: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote candidate profiles or activate runtime, validator, authority, or production behavior.",
            "versions/CHANGELOG.md": "`v1.0.0-rc.7` is the latest released public package. Current public repository\nrelease: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote\ncandidate profiles or activate runtime, validator, authority, deployment, or\nproduction behavior.",
            "07-conformance/verifier-test-suite.md": "status: released",
            "07-conformance/vectors/v1/README.md": "status: released",
        },
    }
    require(release_status in release_markers, f"unsupported public package status: {release_status}")
    state = release_markers[release_status]
    require(state["latest"] in compatibility, "compatibility record latest-release marker missing")
    require(state["compatibility"] in compatibility, "compatibility record release-state marker missing")
    require(not re.search(r"\bN(?:-1|\+1)?\b", compatibility), "generic adjacent-version compatibility heuristic remains")
    require("including this branch" not in compatibility, "branch-relative compatibility wording remains")
    required = {
        "README.md": ("## Release and source state", state["README.md"], "**v1.0.0-rc.5** historical exact reviewed source candidate — not published.", "P4.4 and P9 remain blockers."),
        "SECURITY.md": (REVIEWED_COMMIT, REVIEWED_TREE, "later source is unassigned", state["SECURITY.md"]),
        "protocol/portability/spend-attestation-token.md": ("SpendAttestationTokenV1` and `SpendAttestationTokenV2` are both supported", "no protocol-wide token issuance default"),
        "06-extensions/campaign-experiment-profile.md": ("supported embedded wire/source/binding history, not an observed public tag or public release",),
        "06-extensions/merchant-authority.md": ("supported embedded wire/source/binding history", "not an\nobserved public tag or public release classification"),
        "07-conformance/vectors.md": ("included in released `v1.0.0-rc.3` / suite 2",),
        "07-conformance/verifier-test-suite.md": (state["07-conformance/verifier-test-suite.md"], "The rc.5 candidate\nintentionally fails that gate until P4.4/P9 complete the governed release.", REVIEWED_COMMIT, "later source is unassigned"),
        "07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md": ("This is a source-only candidate bundle", REVIEWED_COMMIT, "later source is unassigned"),
        "08-governance/glossary.md": ("V2 `holderBinding` is\nOPTIONAL, so a V2 token without it remains valid",),
        "08-governance/protocol-v1-index.md": ("released `v1.0.0-rc.3` / conformance suite 2", REVIEWED_COMMIT),
        "08-governance/versioning.md": (state["08-governance/versioning.md"], "Historical exact reviewed source candidate: **1.0.0-rc.5** (`REVIEWED_CANDIDATE_NOT_PUBLISHED`)", "`v1.0.0-rc.3` and `v1.0.0-rc.4` are released public packages; rc.4 is the\nlatest released package."),
        "08-governance/zk-beta-release-checklist.md": ("embedded wire/source/binding history label, not an observed\npublic tag or public-release classification",),
        "versions/CHANGELOG.md": (state["versions/CHANGELOG.md"], "The historical exact reviewed source candidate is **v1.0.0-rc.5**, an\nunpublished SemVer prerelease.", "## v1.0.0-rc.5 release candidate (not published)", "does not promote the W3C profile beyond candidate maturity."),
    }
    for rel, markers in required.items():
        for marker in markers:
            require(marker in documents[rel], f"{rel}: required living wording missing: {marker}")
    require(state["07-conformance/vectors/v1/README.md"] in documents["07-conformance/vectors/v1/README.md"], "conformance README release-state marker missing")
    for rel in ("README.md", "08-governance/versioning.md", "versions/CHANGELOG.md"):
        text = documents[rel]
        require(REVIEWED_COMMIT in text and REVIEWED_TREE in text, f"{rel}: historical rc.5 identity missing")
        require("historical" in text.lower() and "reviewed" in text.lower(), f"{rel}: rc.5 must be explicitly historical and reviewed")
    corpus = "\n".join(documents.values())
    for pattern in (
        r"(?i)unpublished\s+`?v?1\.0\.0-rc\.3`?",
        r"(?i)v1\.0\.0-rc\.3[^\n]{0,90}(?:release candidate|not published)",
        r"(?i)v1\.0\.0-rc\.4[^\n]{0,90}(?:unpublished|release candidate)",
        r"(?i)protocol-wide token issuance default is(?:\s+)?v2",
        r"including this branch",
        r"(?im)^Current public repository source candidate:\s+\*\*v?1\.0\.0-rc\.5",
        r"(?im)^The current public repository release candidate is \*\*v1\.0\.0-rc\.5",
    ):
        require(not re.search(pattern, corpus), f"false living release/issuance classification: {pattern}")


def validate(root: Path, documents: dict[str, str] | None = None, registry: dict[str, Any] | None = None, release_manifest: dict[str, Any] | None = None) -> None:
    release = read_json(root / "versions/release.json") if release_manifest is None else release_manifest
    validate_registry(read_json(root / REGISTRY) if registry is None else registry, release)
    document_status = "RC8_SOURCE_CANDIDATE" if release.get("status") == "RELEASE_CANDIDATE_NOT_PUBLISHED" and release.get("releaseVersion") == "1.0.0-rc.8" else str(release.get("status"))
    documents_to_validate = load_documents(root) if documents is None else documents
    validate_documents(documents_to_validate, document_status)
    if release.get("releaseVersion") == "1.0.0-rc.8":
        require("| `v1.0.0-rc.8` source candidate | Unreviewed suite-5 successor candidate." in documents_to_validate["07-conformance/compatibility.md"], "rc.8 compatibility marker missing")
        require("## Reward-commitment rc.7 publication defect erratum candidate (not published)" in documents_to_validate["versions/CHANGELOG.md"], "rc.8 changelog marker missing")


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
