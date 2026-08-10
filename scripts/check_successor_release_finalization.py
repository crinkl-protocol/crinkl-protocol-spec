#!/usr/bin/env python3
"""Verify and materialize the reviewed rc.7 candidate-to-release transition."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import check_release_registry as release_registry


ROOT = Path(__file__).resolve().parents[1]
BASE = "3568faacf3f0b5d147e6c4034fd0fc47440dc509"
D5 = "8f720f8d4079cf22a5719aaa33f0a38c718809cf"
ADOPTED_MAIN = "52648bae72a8c3b83883392be1c4ae714e4359c3"
P1_CANDIDATE = "9d5a35eb82b1bb0f4b3d24d6f353999945329aaf"
P1_TREE = "a863f6e8e54c536c2bc8c27a3ab8e917ded6dadb"
RELEASE_VERSION = "1.0.0-rc.7"
REQUIRED_TAG = "v1.0.0-rc.7"
LATEST_RELEASED = "1.0.0-rc.4"
ABSENT = {"presence": "ABSENT"}
TAG_TARGET = {
    "tag": REQUIRED_TAG,
    "preTagTarget": "CURRENT_HEAD",
    "postTagTarget": "IMMUTABLE_TAG_MUST_RESOLVE_TO_CURRENT_HEAD",
}
CONTROL_PATHS = {
    "versions/release.json",
    "conformance/vectors/v1/manifest.json",
    "conformance/profiles/spend-token-v1-v2-geography-commitments/manifest.json",
    "conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json",
    "conformance/profiles/object-model-v1/manifest.json",
    "versions/release-registry.json",
    "conformance/compatibility.md",
    "versions/identifier-inventory.json",
    "versions/errata/released-schema-identifier-collisions-v1.json",
}

DOCUMENTATION_TRANSITIONS = [
    {
        "path": "README.md",
        "candidateMarker": "`v1.0.0-rc.4` is the latest released public package. Current public repository\nsource candidate: **v1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),\nconformance suite 4; it is unreviewed, unpublished, not publishable, and does\nnot inherit rc.5 review.",
        "releasedMarker": "`v1.0.0-rc.7` is the latest released public package. Current public repository\nrelease: **v1.0.0-rc.7** (`RELEASED`), conformance suite 4; it preserves the\nexplicit rc.1/rc.2 wire support set and remains independent from runtime,\nvalidator, authority, and production activation.",
    },
    {
        "path": "SECURITY.md",
        "candidateMarker": "- `v1.0.0-rc.7` is the current unreviewed source candidate and conformance\n  suite 4 (`RELEASE_CANDIDATE_NOT_PUBLISHED`); it is unpublished and not\n  publishable until separately reviewed.",
        "releasedMarker": "- `v1.0.0-rc.7` is the released public package and conformance suite 4;\n  release status does not activate runtime, validator, authority, or\n  production behavior.",
    },
    {
        "path": "governance/versioning.md",
        "candidateMarker": "`v1.0.0-rc.4` is the latest released public package. Current public repository source candidate: **1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`), conformance suite 4; it is unreviewed, unpublished, not publishable, and does not inherit rc.5 review.",
        "releasedMarker": "`v1.0.0-rc.7` is the latest released public package. Current public repository release: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote candidate profiles or activate runtime, validator, authority, or production behavior.",
    },
    {
        "path": "versions/CHANGELOG.md",
        "candidateMarker": "`v1.0.0-rc.4` is the latest released public package. Current public repository\nsource candidate: **1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),\nconformance suite 4; it is unreviewed, unpublished, not publishable, and does\nnot inherit rc.5 review.",
        "releasedMarker": "`v1.0.0-rc.7` is the latest released public package. Current public repository\nrelease: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote\ncandidate profiles or activate runtime, validator, authority, deployment, or\nproduction behavior.",
    },
    {
        "path": "versions/v1.0.0-rc.7/snapshot.md",
        "candidateMarker": "# v1.0.0-rc.7 source candidate",
        "releasedMarker": "# v1.0.0-rc.7 release",
    },
    {
        "path": "versions/v1.0.0-rc.7/snapshot.md",
        "candidateMarker": "Status: `RELEASE_CANDIDATE_NOT_PUBLISHED`",
        "releasedMarker": "Status: `RELEASED`",
    },
    {
        "path": "versions/v1.0.0-rc.7/snapshot.md",
        "candidateMarker": "The candidate is unreviewed, unpublished, and not publishable. `v1.0.0-rc.4` remains the latest immutable public release. Historical rc.5 review applies only to its recorded exact commit/tree. Historical rc.6 review remains permanently bound to `fe23ebe959254de095973943698cb6bb4ead6455` / tree `7f3013ff8a8cddcd854cbdfa16a94f69741dac05`; it is not retargeted.",
        "releasedMarker": "This release supersedes `v1.0.0-rc.4` as the latest immutable public package. Historical rc.5 review applies only to its recorded exact commit/tree. Historical rc.6 review remains permanently bound to `fe23ebe959254de095973943698cb6bb4ead6455` / tree `7f3013ff8a8cddcd854cbdfa16a94f69741dac05`; it is not retargeted. Candidate profile maturity and all runtime, validator, authority, deployment, and production states remain separately governed.",
    },
    {
        "path": "conformance/vectors/v1/README.md",
        "candidateMarker": "status: release-candidate",
        "releasedMarker": "status: released",
    },
    {
        "path": "conformance/verifier-test-suite.md",
        "candidateMarker": "status: release-candidate",
        "releasedMarker": "status: released",
    },
    {
        "path": "conformance/verifier-test-suite.md",
        "candidateMarker": "The current rc.7 source candidate uses conformance suite 4 and includes the\ngeography-commitment profile as a required manifest-bound kind.",
        "releasedMarker": "The released rc.7 package uses conformance suite 4 and includes the\ngeography-commitment profile as a required manifest-bound kind; that profile\nremains candidate maturity unless separately released.",
    },
    {
        "path": "conformance/compatibility.md",
        "candidateMarker": "`v1.0.0-rc.4` is the latest released public package",
        "releasedMarker": "`v1.0.0-rc.7` is the latest released public package",
    },
    {
        "path": "conformance/compatibility.md",
        "candidateMarker": "| `v1.0.0-rc.7` source candidate | Current suite-4 source candidate; unreviewed, unpublished, and not publishable. | It does not inherit the rc.5 review and requires a new exact candidate identity and independent review. |",
        "releasedMarker": "| `v1.0.0-rc.7` public release | Latest released suite-4 public package. | It preserves historical rc.5 review boundaries, candidate profile maturity, and separate runtime/production governance. |",
    },
]

INVARIANTS = [
    {"path": "versions/release.json", "pointer": "/releaseVersion", "value": RELEASE_VERSION},
    {"path": "versions/release.json", "pointer": "/requiredTag", "value": REQUIRED_TAG},
    {"path": "versions/release.json", "pointer": "/defaultBindingProtocolVersion", "value": "1.0.0-rc.2"},
    {"path": "versions/release.json", "pointer": "/supportedWireProtocolVersions", "value": ["1.0.0-rc.1", "1.0.0-rc.2"]},
    {"path": "versions/release.json", "pointer": "/conformance/suiteVersion", "value": 4},
    {"path": "versions/release.json", "pointer": "/profiles/2/kind", "value": "credential.spendAttestation.vcdm2.eddsaJcs2022"},
    {"path": "versions/release.json", "pointer": "/profiles/2/maturity", "value": "CANDIDATE"},
    {"path": "versions/release.json", "pointer": "/profiles/3/maturity", "value": "CANDIDATE"},
    {"path": "versions/release.json", "pointer": "/profiles/4/maturity", "value": "CANDIDATE"},
    {"path": "versions/release.json", "pointer": "/profiles/5/kind", "value": "token.spendAttestation.portableV1.zkCommitmentGeography"},
    {"path": "versions/release.json", "pointer": "/profiles/5/maturity", "value": "CANDIDATE"},
    {"path": "conformance/vectors/v1/manifest.json", "pointer": "/releaseVersion", "value": RELEASE_VERSION},
    {"path": "conformance/vectors/v1/manifest.json", "pointer": "/suiteVersion", "value": 4},
    {"path": "conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "pointer": "/maturity", "value": "candidate"},
    {"path": "conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "pointer": "/releasedConformance", "value": False},
    {"path": "conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "pointer": "/claims/release", "value": False},
    {"path": "conformance/profiles/spend-token-v1-v2-geography-commitments/manifest.json", "pointer": "/maturity", "value": "candidate"},
    {"path": "conformance/profiles/spend-token-v1-v2-geography-commitments/manifest.json", "pointer": "/conformanceManifestEntry/status", "value": "PRESENT_IN_RC7_SUITE_4_SOURCE_CANDIDATE"},
]

REQUIRED_CANDIDATE_GATES = [
    "python3 scripts/check_successor_release_finalization.py --mode candidate",
    "python3 scripts/check_release_registry.py --adopted-repo <crinkl-protocol>",
    "python3 scripts/check_living_version_claims.py",
    "python3 scripts/check_released_identifier_erratum.py --adopted-repo <crinkl-protocol>",
    "node conformance/profiles/spend-token-v1-v2-geography-commitments/scripts/check_spend_token_geography_commitments.mjs",
    "node scripts/verify_conformance.mjs --require-kind token.spendAttestation.portableV1.zkCommitmentGeography",
    "python3 scripts/check_drift.py",
]
REQUIRED_PRE_TAG_GATES = [
    "python3 scripts/check_successor_release_finalization.py --mode released",
    "python3 scripts/check_release_registry.py --adopted-repo <crinkl-protocol>",
    "python3 scripts/check_living_version_claims.py",
    "node scripts/verify_conformance.mjs --require-released --require-kind token.spendAttestation.portableV1.zkCommitmentGeography",
    "TAG_v1.0.0-rc.7_MUST_BE_ABSENT",
    "python3 scripts/check_drift.py",
]
REQUIRED_POST_TAG_GATES = [
    "python3 scripts/check_successor_release_finalization.py --mode released --require-tag",
    "python3 scripts/check_release_registry.py --adopted-repo <crinkl-protocol> --require-tag",
    "node scripts/verify_conformance.mjs --require-released --require-kind token.spendAttestation.portableV1.zkCommitmentGeography",
    "IMMUTABLE_TAG_CHECKOUT_PARITY_RERUN",
]
ROLLBACK = {
    "sourceCandidate": "KEEP_SOURCE_CANDIDATE_UNPUBLISHED_UNTAGGED_AND_UNDEPLOYED",
    "beforeTag": "DISCARD_UNCOMMITTED_MATERIALIZATION_AND_RETAIN_REVIEWED_SOURCE_CANDIDATE",
    "afterTag": "NEVER_RETARGET_OR_DELETE_ACCEPTED_TAG_USE_GOVERNED_WITHDRAWAL_OR_SUCCESSOR_RELEASE",
    "runtimeRollback": "NOT_APPLICABLE_RELEASE_DOES_NOT_ACTIVATE_RUNTIME",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"git {' '.join(args)} failed in {root}: {result.stderr.strip()}")
    return result.stdout.strip()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def released_bytes(root: Path, relative: str) -> bytes:
    """Read immutable released bytes from the release tag when available.

    A later source candidate may reorganize living documentation and source
    paths.  The released-artifact check must continue to validate the exact
    tagged package, not reinterpret that candidate layout as a rewrite of the
    released package.
    """
    tagged = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{REQUIRED_TAG}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if tagged.returncode == 0:
        shown = subprocess.run(
            ["git", "-C", str(root), "show", f"{REQUIRED_TAG}:{relative}"],
            capture_output=True,
            check=False,
        )
        require(shown.returncode == 0, f"unable to read released tag path: {relative}")
        return shown.stdout
    return (root / relative).read_bytes()


def render_json(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: JSON root must be an object")
    return value


def adopted_root() -> Path:
    value = os.environ.get("CRINKL_PROTOCOL_ADOPTED_REPO", "/home/azureuser/crinkl-protocol")
    root = Path(value).resolve()
    require(root.is_dir(), f"adopted repository unavailable: {root}")
    return root


def contained(root: Path, commit: str, ancestor: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, ancestor], check=False).returncode == 0


def pointer_parts(pointer: str) -> list[str]:
    require(pointer.startswith("/"), f"invalid JSON pointer: {pointer}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def pointer_get(document: Any, pointer: str) -> Any:
    current = document
    for part in pointer_parts(pointer):
        if isinstance(current, list):
            index = int(part)
            if index >= len(current):
                return ABSENT
            current = current[index]
        elif isinstance(current, dict):
            if part not in current:
                return ABSENT
            current = current[part]
        else:
            return ABSENT
    return current


def pointer_set(document: Any, pointer: str, value: Any) -> None:
    parts = pointer_parts(pointer)
    current = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    if isinstance(current, list):
        current[int(parts[-1])] = value
    else:
        current[parts[-1]] = value


def release_record(release_digest: str, conformance_digest: str) -> dict[str, Any]:
    release_artifact = {
        "path": "versions/release.json",
        "digestAlgorithm": "sha256",
        "digestBasis": "EXACT_GIT_BLOB_BYTES",
        "digest": release_digest,
        "role": "RELEASE_MANIFEST",
    }
    conformance_artifact = {
        "path": "conformance/vectors/v1/manifest.json",
        "digestAlgorithm": "sha256",
        "digestBasis": "EXACT_GIT_BLOB_BYTES",
        "digest": conformance_digest,
        "role": "CONFORMANCE_MANIFEST",
    }
    return {
        "status": "RELEASED",
        "plannedTag": REQUIRED_TAG,
        "actualTag": None,
        "previousRelease": LATEST_RELEASED,
        "source": {"repository": "crinkl-protocol-spec", "tagTarget": TAG_TARGET},
        "releaseManifestArtifact": release_artifact,
        "artifactInventory": [release_artifact, conformance_artifact],
        "wire": {
            "defaultBindingProtocolVersion": "1.0.0-rc.2",
            "supportedWireProtocolVersions": ["1.0.0-rc.1", "1.0.0-rc.2"],
        },
        "conformance": {
            "suite": "crinkl-protocol-conformance",
            "suiteVersion": 4,
            "manifest": "conformance/vectors/v1/manifest.json",
            "manifestDigest": conformance_digest,
        },
        "adoptedSources": [
            {
                "repository": "crinkl-protocol",
                "commit": ADOPTED_MAIN,
                "evidenceState": "PINNED_BY_CANDIDATE_PROFILE_MANIFEST",
            }
        ],
        "authority": {
            "tagState": "TAG_TARGET_MUST_RESOLVE_TO_CURRENT_HEAD",
            "manifestAuthority": "COMPUTED_NOT_AUTHORITY_ACCEPTED",
            "releaseAuthority": "RELEASED_PACKAGE_TAG_TARGET_DECLARED",
            "provenanceCompleteness": "TAG_TARGET_DECLARED",
            "runtimeImplication": "NONE",
            "productionImplication": "NONE",
        },
    }


def expected_machine_transitions(plan: dict[str, Any]) -> list[dict[str, Any]]:
    digests = digest_map(plan)
    return [
        {"path": "versions/release.json", "pointer": "/status", "candidate": "RELEASE_CANDIDATE_NOT_PUBLISHED", "released": "RELEASED"},
        {"path": "conformance/vectors/v1/manifest.json", "pointer": "/releaseStatus", "candidate": "RELEASE_CANDIDATE_NOT_PUBLISHED", "released": "RELEASED"},
        {"path": "versions/release-registry.json", "pointer": "/latestReleasedVersion", "candidate": LATEST_RELEASED, "released": RELEASE_VERSION},
        {"path": "versions/release-registry.json", "pointer": "/candidateState", "candidate": "SOURCE_CANDIDATE_AWAITING_REVIEW_NOT_PUBLISHABLE", "released": "NO_ACTIVE_OR_PUBLISHABLE_CANDIDATE"},
        {"path": "versions/release-registry.json", "pointer": "/releases/1.0.0-rc.7", "candidate": ABSENT, "released": release_record(digests["versions/release.json"], digests["conformance/vectors/v1/manifest.json"])},
    ]


def digest_map(plan: dict[str, Any]) -> dict[str, str]:
    items = plan.get("releasedArtifactDigests")
    require(isinstance(items, list), "released artifact digest map missing")
    result: dict[str, str] = {}
    for item in items:
        require(isinstance(item, dict), "released artifact digest item must be an object")
        path, digest = item.get("path"), item.get("sha256")
        require(isinstance(path, str) and isinstance(digest, str), "released artifact digest item shape drift")
        require(path not in result and digest.startswith("sha256:") and len(digest) == 71, "released artifact digest map drift")
        result[path] = digest
    expected_paths = {item["path"] for item in DOCUMENTATION_TRANSITIONS} | {
        "versions/release.json",
        "conformance/vectors/v1/manifest.json",
        "versions/release-registry.json",
    }
    require(set(result) == expected_paths, "released artifact digest path set drift")
    return result


def validate_plan(plan: dict[str, Any]) -> None:
    require(plan.get("kind") == "crinkl.protocol.releaseFinalizationPlanV1" and plan.get("planVersion") == 2, "finalization plan identity drift")
    require(plan.get("releaseVersion") == RELEASE_VERSION and plan.get("requiredTag") == REQUIRED_TAG, "rc.7 finalization version drift")
    require(plan.get("latestReleasedVersion") == LATEST_RELEASED and plan.get("previousRelease") == LATEST_RELEASED, "rc.7 predecessor drift")
    require(plan.get("requiredProductionAuthorization") == "PRODUCTION-OPS OK", "production authorization control drift")
    require(plan.get("candidateState") == "SOURCE_CANDIDATE_AWAITING_REVIEW_NOT_PUBLISHABLE", "source candidate state drift")
    require(plan.get("rollback") == ROLLBACK, "rollback boundary drift")
    require(plan.get("sourceComposition") == {
        "publicMainBase": BASE,
        "d5CompatibilityHead": D5,
        "adoptedMain": ADOPTED_MAIN,
        "reviewedNotContainedByAdoptedMain": [],
        "adoptedMainContains": [P1_CANDIDATE],
    }, "candidate source composition drift")
    controls = plan.get("controllingArtifacts")
    require(isinstance(controls, list) and controls, "controlling artifact set missing")
    paths = [item.get("path") for item in controls if isinstance(item, dict)]
    require(len(paths) == len(controls) and len(paths) == len(set(paths)) and set(paths) == CONTROL_PATHS, "control set must contain exactly the required artifacts")
    digest_map(plan)
    require(plan.get("machineTransitions") == expected_machine_transitions(plan), "machine transition contract drift")
    require(plan.get("invariants") == INVARIANTS, "release invariant contract drift")
    require(plan.get("documentationTransitions") == DOCUMENTATION_TRANSITIONS, "documentation transition contract drift")
    require(plan.get("requiredCandidateGates") == REQUIRED_CANDIDATE_GATES, "candidate gate contract drift")
    require(plan.get("requiredPreTagGates") == REQUIRED_PRE_TAG_GATES, "pre-tag gate contract drift")
    require(plan.get("requiredPostTagGates") == REQUIRED_POST_TAG_GATES, "post-tag gate contract drift")
    require(plan.get("transitionPathCount") == 11 and plan.get("machineTransitionCount") == 5 and plan.get("documentationTransitionCount") == 14, "transition count drift")


def validate_candidate_runtime(root: Path, plan: dict[str, Any]) -> dict[str, str]:
    release = read_json(root / "versions/release.json")
    manifest = read_json(root / "conformance/vectors/v1/manifest.json")
    require(release.get("releaseVersion") == RELEASE_VERSION and release.get("status") == "RELEASE_CANDIDATE_NOT_PUBLISHED", "release manifest candidate drift")
    require(release.get("requiredTag") == REQUIRED_TAG and release.get("supportedWireProtocolVersions") == ["1.0.0-rc.1", "1.0.0-rc.2"], "release manifest wire/tag drift")
    require(release.get("conformance", {}).get("suiteVersion") == 4, "release manifest suite drift")
    require(manifest.get("releaseVersion") == RELEASE_VERSION and manifest.get("releaseStatus") == release.get("status") and manifest.get("suiteVersion") == 4, "conformance manifest candidate drift")
    require(not release_registry.tag_ref_exists(root, REQUIRED_TAG), "source candidate must remain untagged")
    require(git(root, "merge-base", "--is-ancestor", BASE, "HEAD") == "", "candidate does not descend from public-main base")
    git(root, "cat-file", "-e", f"{D5}^{{commit}}")
    adopted = adopted_root()
    for commit in (ADOPTED_MAIN, P1_CANDIDATE):
        git(adopted, "cat-file", "-e", f"{commit}^{{commit}}")
    require(contained(adopted, P1_CANDIDATE, ADOPTED_MAIN), "adopted main does not contain exact P1 candidate")
    require(git(adopted, "rev-parse", f"{P1_CANDIDATE}^{{tree}}") == P1_TREE, "P1 candidate tree drift")
    require(git(adopted, "rev-parse", f"{ADOPTED_MAIN}^{{tree}}") == P1_TREE, "adopted main tree drift")
    for relative, kind in {
        "conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json": "credential.spendAttestation.vcdm2.eddsaJcs2022",
        "conformance/profiles/spend-token-v1-v2-geography-commitments/manifest.json": "token.spendAttestation.portableV1.zkCommitmentGeography",
    }.items():
        profile = read_json(root / relative)
        require(profile.get("engineeringSource") == {
            "repository": "crinkl-protocol", "commit": ADOPTED_MAIN, "maturity": "engineering-adopted-on-protected-main",
        }, f"adopted source pin drift: {kind}")
    digests: dict[str, str] = {}
    for item in plan["controllingArtifacts"]:
        path, expected = item.get("path"), item.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), "control artifact shape drift")
        actual = sha256(root / path)
        require(actual == expected, f"controlling artifact digest drift: {path}")
        digests[path] = actual
    check_documentation(root, plan, "candidate")
    return digests


def check_documentation(root: Path, plan: dict[str, Any], mode: str, texts: dict[str, str] | None = None) -> None:
    for transition in plan["documentationTransitions"]:
        path = str(transition["path"])
        text = texts[path] if texts is not None else (root / path).read_text(encoding="utf-8")
        required = str(transition["candidateMarker" if mode == "candidate" else "releasedMarker"])
        forbidden = str(transition["releasedMarker" if mode == "candidate" else "candidateMarker"])
        require(text.count(required) == 1 and forbidden not in text, f"{mode} documentation marker mismatch: {path}")


def materialize_released(root: Path, plan: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, bytes]]:
    json_documents: dict[str, dict[str, Any]] = {}
    for transition in plan["machineTransitions"]:
        path = str(transition["path"])
        document = json_documents.setdefault(path, read_json(root / path))
        observed = pointer_get(document, str(transition["pointer"]))
        require(observed == transition["candidate"], f"candidate machine transition mismatch: {path}{transition['pointer']}")
        pointer_set(document, str(transition["pointer"]), copy.deepcopy(transition["released"]))
    for invariant in plan["invariants"]:
        path = str(invariant["path"])
        document = json_documents.setdefault(path, read_json(root / path))
        require(pointer_get(document, str(invariant["pointer"])) == invariant["value"], f"release invariant mismatch: {path}{invariant['pointer']}")
    texts: dict[str, str] = {}
    for transition in plan["documentationTransitions"]:
        path = str(transition["path"])
        text = texts.setdefault(path, (root / path).read_text(encoding="utf-8"))
        candidate, released = str(transition["candidateMarker"]), str(transition["releasedMarker"])
        require(text.count(candidate) == 1 and released not in text, f"candidate documentation simulation mismatch: {path}")
        texts[path] = text.replace(candidate, released, 1)
    check_documentation(root, plan, "released", texts)
    machine_paths = {str(transition["path"]) for transition in plan["machineTransitions"]}
    rendered = {path: render_json(document) for path, document in json_documents.items() if path in machine_paths}
    rendered.update({path: text.encode("utf-8") for path, text in texts.items()})
    observed_digests = {path: sha256_bytes(value) for path, value in sorted(rendered.items())}
    require(observed_digests == digest_map(plan), "simulated released artifact digest map drift")
    return json_documents, texts, rendered


def validate_materialized_release(
    root: Path,
    plan: dict[str, Any],
    json_documents: dict[str, dict[str, Any]],
    rendered: dict[str, bytes],
    *,
    require_tag: bool,
) -> None:
    release = json_documents["versions/release.json"]
    registry = json_documents["versions/release-registry.json"]
    require(release.get("status") == "RELEASED", "simulated release manifest status drift")
    require(registry.get("candidateState") == "NO_ACTIVE_OR_PUBLISHABLE_CANDIDATE", "simulated registry candidate state drift")
    require(registry.get("latestReleasedVersion") == RELEASE_VERSION and registry.get("reviewedCandidateVersion") == "1.0.0-rc.5", "simulated registry release history drift")
    record = registry.get("releases", {}).get(RELEASE_VERSION)
    require(isinstance(record, dict) and record.get("previousRelease") == LATEST_RELEASED, "simulated rc.7 predecessor drift")
    require(record.get("source") == {"repository": "crinkl-protocol-spec", "tagTarget": TAG_TARGET}, "simulated tag-target source drift")
    errors = release_registry.validate_registry(
        root,
        read_json(root / "versions/release-ledger.schema.json"),
        registry,
        release,
        adopted_root(),
        require_tag=require_tag,
        materialized_documents=rendered,
    )
    require(not errors, "simulated release registry invalid: " + "; ".join(errors))
    for invariant in INVARIANTS:
        path, pointer, value = invariant["path"], invariant["pointer"], invariant["value"]
        document = json_documents.get(path) or read_json(root / path)
        require(pointer_get(document, pointer) == value, f"materialized invariant drift: {path}{pointer}")


def validate_materialized_workspace(root: Path, plan: dict[str, Any], *, require_tag: bool) -> tuple[dict[str, dict[str, Any]], dict[str, bytes]]:
    require(git(root, "status", "--porcelain") == "", "materialized release verification requires a clean committed workspace")
    json_paths = {str(transition["path"]) for transition in plan["machineTransitions"]}
    json_documents = {
        path: json.loads(released_bytes(root, path).decode("utf-8"))
        for path in json_paths
    }
    for transition in plan["machineTransitions"]:
        path = str(transition["path"])
        require(
            pointer_get(json_documents[path], str(transition["pointer"])) == transition["released"],
            f"released machine transition mismatch: {path}{transition['pointer']}",
        )
    texts = {
        str(transition["path"]): released_bytes(root, str(transition["path"])).decode("utf-8")
        for transition in plan["documentationTransitions"]
    }
    check_documentation(root, plan, "released", texts)
    rendered = {path: render_json(document) for path, document in json_documents.items()}
    rendered.update({path: text.encode("utf-8") for path, text in texts.items()})
    observed_digests = {path: sha256_bytes(value) for path, value in sorted(rendered.items())}
    require(observed_digests == digest_map(plan), "materialized released artifact digest map drift")
    validate_materialized_release(root, plan, json_documents, rendered, require_tag=require_tag)
    return json_documents, rendered


def release_identity(root: Path, plan: dict[str, Any], rendered: dict[str, bytes]) -> str:
    identity = {
        "releaseVersion": RELEASE_VERSION,
        "requiredTag": REQUIRED_TAG,
        "sourceCandidateHead": git(root, "rev-parse", "HEAD"),
        "sourceCandidateTree": git(root, "rev-parse", "HEAD^{tree}"),
        "tagTarget": TAG_TARGET,
        "artifactDigests": {path: sha256_bytes(value) for path, value in sorted(rendered.items())},
    }
    return "sha256:" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def candidate_identity(root: Path, plan: dict[str, Any], controls: dict[str, str]) -> str:
    identity = {
        "releaseVersion": RELEASE_VERSION,
        "requiredTag": REQUIRED_TAG,
        "head": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "controls": controls,
        "transitionDigestMap": digest_map(plan),
    }
    return "sha256:" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def assert_tamper_rejected(root: Path, plan: dict[str, Any]) -> None:
    probes: list[dict[str, Any]] = []
    removed_transition = copy.deepcopy(plan)
    removed_transition["machineTransitions"].pop()
    probes.append(removed_transition)
    changed_marker = copy.deepcopy(plan)
    changed_marker["documentationTransitions"][0]["releasedMarker"] = "unbounded release wording"
    probes.append(changed_marker)
    weakened_gate = copy.deepcopy(plan)
    weakened_gate["requiredPostTagGates"] = weakened_gate["requiredPostTagGates"][:-1]
    probes.append(weakened_gate)
    promoted_profile = copy.deepcopy(plan)
    promoted_profile["invariants"][6]["value"] = "RELEASED"
    probes.append(promoted_profile)
    for probe in probes:
        try:
            validate_plan(probe)
        except ValueError:
            continue
        raise ValueError("release finalization tamper probe unexpectedly passed")
    materialized, _, rendered = materialize_released(root, plan)
    errors = release_registry.validate_registry(
        root,
        read_json(root / "versions/release-ledger.schema.json"),
        copy.deepcopy(materialized["versions/release-registry.json"]),
        copy.deepcopy(materialized["versions/release.json"]),
        adopted_root(),
        require_tag=True,
        materialized_documents=rendered,
    )
    require(any("required immutable tag is absent" in item for item in errors), "missing required tag was accepted")
    tampered_registry = copy.deepcopy(materialized["versions/release-registry.json"])
    tampered_registry["releases"][RELEASE_VERSION]["source"]["tagTarget"]["preTagTarget"] = "ARBITRARY_COMMIT"
    errors = release_registry.validate_registry(
        root,
        read_json(root / "versions/release-ledger.schema.json"),
        tampered_registry,
        copy.deepcopy(materialized["versions/release.json"]),
        adopted_root(),
        materialized_documents=rendered,
    )
    require(errors, "tag-target tamper was accepted")


def write_materialization(root: Path, rendered: dict[str, bytes]) -> None:
    for path, content in rendered.items():
        (root / path).write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("candidate", "released"), default="candidate")
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--write-materialized-release",
        action="store_true",
        help="Apply only the reviewed release transitions after candidate review and before the immutable tag is created.",
    )
    args = parser.parse_args()
    require(not args.require_tag or args.mode == "released", "--require-tag requires --mode released")
    require(not args.write_materialized_release or args.mode == "released", "--write-materialized-release requires --mode released")
    plan = read_json(ROOT / "versions/v1.0.0-rc.7/finalization.json")
    validate_plan(plan)
    physical_status = read_json(ROOT / "versions/release.json").get("status")
    controls: dict[str, str] | None = None
    if physical_status == "RELEASE_CANDIDATE_NOT_PUBLISHED":
        controls = validate_candidate_runtime(ROOT, plan)
        materialized, _, rendered = materialize_released(ROOT, plan)
        validate_materialized_release(ROOT, plan, materialized, rendered, require_tag=args.require_tag)
    elif physical_status == "RELEASED" and args.mode == "released":
        _, rendered = validate_materialized_workspace(ROOT, plan, require_tag=args.require_tag)
    else:
        raise ValueError("candidate mode requires source-candidate bytes; released mode requires candidate or materialized released bytes")
    if args.self_test:
        require(controls is not None, "self-test requires source-candidate bytes")
        assert_tamper_rejected(ROOT, plan)
    if args.write_materialized_release:
        require(controls is not None, "materialization requires source-candidate bytes")
        write_materialization(ROOT, rendered)
        print("[successor-release-finalization] materialized reviewed release transitions; commit and run pre-tag gates before tagging")
        return 0
    simulated = release_identity(ROOT, plan, rendered)
    source = candidate_identity(ROOT, plan, controls) if controls is not None else "not-applicable-materialized-release"
    if args.mode == "candidate":
        print(f"[successor-release-finalization] OK (candidate; sourceCandidateIdentity={source}; simulatedReleasedIdentity={simulated})")
    else:
        print(f"[successor-release-finalization] OK (released simulation; sourceCandidateIdentity={source}; simulatedReleasedIdentity={simulated}; tagRequired={str(args.require_tag).lower()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
