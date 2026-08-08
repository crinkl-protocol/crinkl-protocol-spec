#!/usr/bin/env python3
"""Verify the active successor release plan without rewriting historical plans."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ENGINEERING_SOURCE = {
    "repository": "crinkl-protocol",
    "commit": "ae6382f1ed11b88f9bbfdcc4ef12119647cc7698",
    "adoptionRule": "PROTECTED_MAIN_MUST_CONTAIN_EXACT_COMMIT",
}
MACHINE_TRANSITIONS = [
    ("versions/release.json", "/status", "RELEASE_CANDIDATE_NOT_PUBLISHED", "RELEASED"),
    ("07-conformance/vectors/v1/manifest.json", "/releaseStatus", "RELEASE_CANDIDATE_NOT_PUBLISHED", "RELEASED"),
    ("versions/release.json", "/profiles/2/maturity", "CANDIDATE", "RELEASED"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/maturity", "candidate", "released"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/releasedConformance", False, True),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/conformanceManifestEntry/status", "PRESENT_IN_RC5_SUITE_3_SOURCE_CANDIDATE", "PRESENT_IN_RELEASED_RC5_SUITE_3"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/publicationBlockers", ["P4.4_EXACT_PUBLIC_CANDIDATE_REVIEW", "P9_ACCEPTED_PUBLIC_RELEASE"], []),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/claims/release", False, True),
]
INVARIANTS = [
    ("versions/release.json", "/releaseVersion", "1.0.0-rc.5"),
    ("versions/release.json", "/requiredTag", "v1.0.0-rc.5"),
    ("versions/release.json", "/conformance/suiteVersion", 3),
    ("versions/release.json", "/profiles/2/kind", "credential.spendAttestation.vcdm2.eddsaJcs2022"),
    ("07-conformance/vectors/v1/manifest.json", "/suiteVersion", 3),
    ("07-conformance/vectors/v1/manifest.json", "/vectors/14/kind", "credential.spendAttestation.vcdm2.eddsaJcs2022"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/claims/runtime", False),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json", "/claims/production", False),
]
DOCUMENTATION_TRANSITIONS = [
    ("README.md", "**v1.0.0-rc.5** release candidate source — not yet published.", "**v1.0.0-rc.5** — released."),
    ("08-governance/versioning.md", "Current public repository source candidate: **1.0.0-rc.5** (`RELEASE_CANDIDATE_NOT_PUBLISHED`)", "Current public repository release: **1.0.0-rc.5** (`RELEASED`)"),
    ("versions/v1.0.0-rc.5/snapshot.md", "Status: `RELEASE_CANDIDATE_NOT_PUBLISHED`", "Status: `RELEASED`"),
    ("07-conformance/vectors/v1/README.md", "status: release-candidate", "status: released"),
    ("07-conformance/verifier-test-suite.md", "status: release-candidate", "status: released"),
    ("versions/CHANGELOG.md", "## v1.0.0-rc.5 release candidate (not published)", "## v1.0.0-rc.5 ("),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "status: draft", "status: released"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "Profile release state: candidate.", "Profile release state: released."),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "Publication state: P4.4 exact-candidate review and P9 accepted public-release authority remain blockers.", "Publication state: P4.4 exact-candidate review and P9 accepted public-release authority are complete for this release."),
    ("README.md", "## Verify the Candidate Native V1 Fixture", "## Verify the Released Native V1 Fixture"),
    ("README.md", "This is an unpublished SemVer prerelease candidate, not a stable `v1.0.0`", "This is a released SemVer prerelease package, not a stable `v1.0.0`"),
    ("README.md", "P4.4 and P9 remain blockers.", "P4.4 and P9 are complete."),
    ("README.md", "python3 scripts/check_successor_release_finalization.py --mode candidate", "python3 scripts/check_successor_release_finalization.py --mode released --require-tag"),
    ("08-governance/versioning.md", "unpublished SemVer prerelease candidate", "released SemVer prerelease package"),
    ("versions/CHANGELOG.md", "current public repository release candidate is **v1.0.0-rc.5**, an\nunpublished SemVer prerelease.", "current public repository release is **v1.0.0-rc.5**, a released\nSemVer prerelease package."),
    ("versions/CHANGELOG.md", "runtime, release, and production remain unclaimed.", "runtime and production remain unclaimed; the profile release is recorded by this package."),
    ("versions/CHANGELOG.md", "does not promote the W3C profile beyond candidate maturity.", "records the W3C profile as released while preserving its runtime and production nonclaims."),
    ("versions/v1.0.0-rc.5/snapshot.md", "- Public repository release: `1.0.0-rc.5` candidate.", "- Public repository release: `1.0.0-rc.5` released."),
    ("versions/v1.0.0-rc.5/snapshot.md", "The candidate does not relabel or", "The release does not relabel or"),
    ("versions/v1.0.0-rc.5/snapshot.md", "The profile remains candidate-only", "The profile is released"),
    ("versions/v1.0.0-rc.5/snapshot.md", "This candidate does not activate", "This release does not activate"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "# W3C VC 2.0 Spend Attestation candidate bundle", "# W3C VC 2.0 Spend Attestation profile bundle"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "This is a source-only candidate bundle", "This is a released profile bundle"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "unpublished `v1.0.0-rc.5`", "released `v1.0.0-rc.5`"),
    ("07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/README.md", "runtime adoption, QA, release, and production", "runtime adoption, QA, and production"),
    ("07-conformance/verifier-test-suite.md", "candidate W3C Spend Attestation fixture harness", "released W3C Spend Attestation fixture harness"),
    ("07-conformance/verifier-test-suite.md", "rc.5 candidate\nintentionally fails that gate until P4.4/P9 complete the governed release.", "released rc.5 manifest must pass that gate."),
    ("07-conformance/verifier-test-suite.md", "This is candidate\n  fixture coverage only;", "This is released fixture coverage;"),
    ("07-conformance/vectors/v1/README.md", "candidate\n  only and not a generic VC/VP API or runtime authorization", "released profile coverage and not a generic VC/VP API or runtime authorization"),
]
REQUIRED_CANDIDATE_GATES = [
    "python3 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_vc_2_0_spend_attestation_bundle.py", "node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_spend_attestation_credential_vectors.mjs", "node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/generate_w3c_bitstring_status_list_vectors.mjs", "node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_bitstring_status_list_vectors.mjs", "node 07-conformance/profiles/spend-token-v2-holder-binding/scripts/check_holder_binding_vectors.mjs", "python3 scripts/check_successor_release_finalization.py --mode candidate", "python3 scripts/check_drift.py", "node scripts/verify_conformance.mjs --require-kind credential.spendAttestation.vcdm2.eddsaJcs2022", "CROSS_REPOSITORY_W3C_ARTIFACT_SHA256_PARITY", "ENGINEERING_PROTECTED_MAIN_CONTAINS_EXACT_COMMIT",
]
REQUIRED_PRE_TAG_GATES = [
    "python3 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_vc_2_0_spend_attestation_bundle.py", "node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_spend_attestation_credential_vectors.mjs", "node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/generate_w3c_bitstring_status_list_vectors.mjs", "node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_bitstring_status_list_vectors.mjs", "node 07-conformance/profiles/spend-token-v2-holder-binding/scripts/check_holder_binding_vectors.mjs", "python3 scripts/check_successor_release_finalization.py --mode released", "python3 scripts/check_drift.py", "node scripts/verify_conformance.mjs --require-released --require-kind credential.spendAttestation.vcdm2.eddsaJcs2022", "CROSS_REPOSITORY_W3C_ARTIFACT_SHA256_PARITY", "ENGINEERING_PROTECTED_MAIN_CONTAINS_EXACT_COMMIT",
]
REQUIRED_POST_TAG_GATES = [
    "python3 scripts/check_successor_release_finalization.py --mode released --require-tag", "node scripts/verify_conformance.mjs --require-released --require-kind credential.spendAttestation.vcdm2.eddsaJcs2022", "IMMUTABLE_TAG_CHECKOUT_PARITY_RERUN",
]
ROLLBACK = {"beforeTag": "DO_NOT_PUBLISH_AND_KEEP_STATUS_CANDIDATE", "afterTag": "NEVER_RETARGET_OR_DELETE_ACCEPTED_TAG_USE_GOVERNED_WITHDRAWAL_OR_SUCCESSOR_RELEASE", "runtimeRollback": "NOT_APPLICABLE_RELEASE_DOES_NOT_ACTIVATE_RUNTIME"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pointer_parts(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def pointer_get(document: Any, pointer: str) -> Any:
    current = document
    for part in pointer_parts(pointer):
        current = current[int(part)] if isinstance(current, list) else current[part]
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


def rendered_sha256(document: dict[str, Any]) -> str:
    return hashlib.sha256((json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")).hexdigest()


def check_documentation(repo_root: Path, plan: dict[str, Any], mode: str) -> None:
    for transition in plan.get("documentationTransitions") or []:
        text = (repo_root / str(transition["path"])).read_text(encoding="utf-8")
        required = str(transition["candidateMarker" if mode == "candidate" else "releasedMarker"])
        forbidden = str(transition["releasedMarker" if mode == "candidate" else "candidateMarker"])
        if text.count(required) != 1 or forbidden in text:
            raise ValueError(f"{mode} documentation marker mismatch: {transition['path']}")


def simulated_released_documentation_sha256(
    repo_root: Path, plan: dict[str, Any]
) -> dict[str, str]:
    documents: dict[str, str] = {}
    for transition in plan.get("documentationTransitions") or []:
        path = str(transition["path"])
        text = documents.setdefault(path, (repo_root / path).read_text(encoding="utf-8"))
        candidate = str(transition["candidateMarker"])
        released = str(transition["releasedMarker"])
        if text.count(candidate) != 1 or released in text:
            raise ValueError(f"candidate documentation simulation mismatch: {path}")
        documents[path] = text.replace(candidate, released, 1)

    for transition in plan.get("documentationTransitions") or []:
        path = str(transition["path"])
        text = documents[path]
        candidate = str(transition["candidateMarker"])
        released = str(transition["releasedMarker"])
        if candidate in text or text.count(released) != 1:
            raise ValueError(f"released documentation simulation mismatch: {path}")

    return {
        path: hashlib.sha256(text.encode("utf-8")).hexdigest()
        for path, text in sorted(documents.items())
    }


def check_tag(repo_root: Path, tag: str) -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, text=True, capture_output=True).stdout.strip()
    tagged = subprocess.run(["git", "rev-parse", f"refs/tags/{tag}^{{commit}}"], cwd=repo_root, check=True, text=True, capture_output=True).stdout.strip()
    if head != tagged:
        raise ValueError(f"release tag does not identify HEAD: tag={tagged} head={head}")


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("kind") != "crinkl.protocol.releaseFinalizationPlanV1" or plan.get("planVersion") != 1:
        raise ValueError("release finalization plan identity drift")
    if plan.get("releaseVersion") != "1.0.0-rc.5" or plan.get("requiredTag") != "v1.0.0-rc.5":
        raise ValueError("release finalization version drift")
    if plan.get("requiredProductionAuthorization") != "PRODUCTION-OPS OK" or plan.get("engineeringSource") != ENGINEERING_SOURCE or plan.get("rollback") != ROLLBACK:
        raise ValueError("release finalization authority or rollback drift")
    actual_transitions = [(item.get("path"), item.get("pointer"), item.get("candidate"), item.get("released")) for item in plan.get("machineTransitions") or []]
    actual_invariants = [(item.get("path"), item.get("pointer"), item.get("value")) for item in plan.get("invariants") or []]
    actual_docs = [(item.get("path"), item.get("candidateMarker"), item.get("releasedMarker")) for item in plan.get("documentationTransitions") or []]
    if actual_transitions != MACHINE_TRANSITIONS or actual_invariants != INVARIANTS or actual_docs != DOCUMENTATION_TRANSITIONS:
        raise ValueError("release finalization transition contract drift")
    if plan.get("requiredCandidateGates") != REQUIRED_CANDIDATE_GATES or plan.get("requiredPreTagGates") != REQUIRED_PRE_TAG_GATES or plan.get("requiredPostTagGates") != REQUIRED_POST_TAG_GATES:
        raise ValueError("release finalization gate contract drift")


def assert_tamper_rejected(plan: dict[str, Any]) -> None:
    probes = []
    removed_transition = copy.deepcopy(plan)
    removed_transition["machineTransitions"].pop()
    probes.append(removed_transition)
    weakened_gate = copy.deepcopy(plan)
    weakened_gate["requiredPreTagGates"] = weakened_gate["requiredPreTagGates"][:-1]
    probes.append(weakened_gate)
    changed_marker = copy.deepcopy(plan)
    changed_marker["documentationTransitions"][0]["candidateMarker"] = "unbounded marker"
    probes.append(changed_marker)
    for probe in probes:
        try:
            validate_plan(probe)
        except ValueError:
            continue
        raise ValueError("release finalization tamper probe unexpectedly passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("candidate", "released"), default="candidate")
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.require_tag and args.mode != "released":
        raise ValueError("--require-tag requires --mode released")

    repo_root = Path(__file__).resolve().parents[1]
    release = read_json(repo_root / "versions" / "release.json")
    version = str(release.get("releaseVersion") or "")
    plan = read_json(repo_root / "versions" / f"v{version}" / "finalization.json")
    validate_plan(plan)
    if args.self_test:
        assert_tamper_rejected(plan)
    if plan.get("releaseVersion") != version or plan.get("requiredTag") != f"v{version}":
        raise ValueError("release finalization identity drift")
    if release.get("requiredTag") != plan["requiredTag"]:
        raise ValueError("release manifest tag drift")

    documents: dict[str, dict[str, Any]] = {}
    for transition in plan.get("machineTransitions") or []:
        path = str(transition["path"])
        document = documents.setdefault(path, read_json(repo_root / path))
        expected = transition[args.mode]
        if pointer_get(document, str(transition["pointer"])) != expected:
            raise ValueError(f"{args.mode} machine transition mismatch: {path}{transition['pointer']}")
    for invariant in plan.get("invariants") or []:
        path = str(invariant["path"])
        document = documents.setdefault(path, read_json(repo_root / path))
        if pointer_get(document, str(invariant["pointer"])) != invariant["value"]:
            raise ValueError(f"release invariant mismatch: {path}{invariant['pointer']}")
    check_documentation(repo_root, plan, args.mode)

    if args.mode == "candidate":
        simulated = copy.deepcopy(documents)
        for transition in plan.get("machineTransitions") or []:
            pointer_set(simulated[str(transition["path"])], str(transition["pointer"]), transition["released"])
        identity = {
            "releaseVersion": version,
            "requiredTag": plan["requiredTag"],
            "engineeringSource": plan["engineeringSource"],
            "machineFileSha256": {path: rendered_sha256(document) for path, document in sorted(simulated.items())},
            "documentationFileSha256": simulated_released_documentation_sha256(repo_root, plan),
        }
        digest = hashlib.sha256(json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
        print(f"[successor-release-finalization] OK (candidate; simulatedReleaseIdentity=sha256:{digest})")
    else:
        if args.require_tag:
            check_tag(repo_root, str(plan["requiredTag"]))
        print(f"[successor-release-finalization] OK (released; tagRequired={str(args.require_tag).lower()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
