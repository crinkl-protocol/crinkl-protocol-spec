#!/usr/bin/env python3
"""Verify the rc.6 source-candidate composition and finalization controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = "3568faacf3f0b5d147e6c4034fd0fc47440dc509"
D5 = "8f720f8d4079cf22a5719aaa33f0a38c718809cf"
ADOPTED_MAIN = "5b7ee08e624772f097346e1cff9e71c40086b376"
D1 = "24befee1205f65c7b84eca33f2720862a00a89c5"
D3 = "4ae7261c4b29de046ce268a3be126b92683579ec"
W3C = "ae6382f1ed11b88f9bbfdcc4ef12119647cc7698"
GEOGRAPHY = "12337aa2c688ef0fe4cd275d6f791e5a4eda4a16"
LATEST_RELEASED = "1.0.0-rc.4"
CONTROL_PATHS = {
    "versions/release.json",
    "07-conformance/vectors/v1/manifest.json",
    "07-conformance/profiles/spend-token-v1-v2-geography-commitments/manifest.json",
    "07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/manifest.json",
    "07-conformance/profiles/object-model-v1/manifest.json",
    "versions/release-registry.json",
    "07-conformance/compatibility.md",
    "versions/identifier-inventory.json",
    "versions/errata/released-schema-identifier-collisions-v1.json",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"git {' '.join(args)} failed in {root}: {result.stderr.strip()}")
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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


def validate(plan: dict[str, Any]) -> None:
    require(plan.get("kind") == "crinkl.protocol.releaseFinalizationPlanV1" and plan.get("planVersion") == 1, "finalization plan identity drift")
    require(plan.get("releaseVersion") == "1.0.0-rc.6" and plan.get("requiredTag") == "v1.0.0-rc.6", "rc.6 finalization version drift")
    require(
        plan.get("latestReleasedVersion") == LATEST_RELEASED and plan.get("previousRelease") == LATEST_RELEASED,
        "rc.6 finalization predecessor drift",
    )
    require(plan.get("requiredProductionAuthorization") == "PRODUCTION-OPS OK", "production authorization control drift")
    require(plan.get("candidateState") == "SOURCE_CANDIDATE_AWAITING_REVIEW_NOT_PUBLISHABLE", "candidate state drift")
    require(plan.get("rollback") == "DO_NOT_PUBLISH_OR_TAG_SOURCE_CANDIDATE", "candidate rollback control drift")
    composition = plan.get("sourceComposition")
    require(composition == {
        "publicMainBase": BASE, "d5CompatibilityHead": D5,
        "adoptedMain": ADOPTED_MAIN,
        "reviewedNotContainedByAdoptedMain": [D1, D3],
        "adoptedMainContains": [W3C, GEOGRAPHY],
    }, "candidate source composition drift")
    controls = plan.get("controllingArtifacts")
    require(isinstance(controls, list) and controls, "controlling artifact set missing")
    paths = [item.get("path") for item in controls if isinstance(item, dict)]
    require(
        len(paths) == len(controls) and len(paths) == len(set(paths)) and set(paths) == CONTROL_PATHS,
        "control set must contain exactly the required artifacts",
    )


def validate_runtime(plan: dict[str, Any]) -> dict[str, str]:
    release = read_json(ROOT / "versions/release.json")
    manifest = read_json(ROOT / "07-conformance/vectors/v1/manifest.json")
    require(release.get("releaseVersion") == "1.0.0-rc.6" and release.get("status") == "RELEASE_CANDIDATE_NOT_PUBLISHED", "release manifest candidate drift")
    require(release.get("requiredTag") == "v1.0.0-rc.6" and release.get("supportedWireProtocolVersions") == ["1.0.0-rc.1", "1.0.0-rc.2"], "release manifest wire/tag drift")
    require(release.get("conformance", {}).get("suiteVersion") == 4, "release manifest suite drift")
    require(manifest.get("releaseVersion") == "1.0.0-rc.6" and manifest.get("releaseStatus") == release.get("status") and manifest.get("suiteVersion") == 4, "conformance manifest candidate drift")
    kinds = [entry.get("kind") for entry in manifest.get("vectors", []) if isinstance(entry, dict)]
    for kind in ("token.spendAttestation.holderBinding.v2", "credential.spendAttestation.vcdm2.eddsaJcs2022", "schema.objectModel.om4.v1", "token.spendAttestation.portableV1.zkCommitmentGeography"):
        require(kind in kinds, f"required suite-4 kind missing: {kind}")
    require(git(ROOT, "merge-base", "--is-ancestor", BASE, "HEAD") == "", "candidate does not descend from public-main base")
    require(git(ROOT, "merge-base", "--is-ancestor", D5, "HEAD") == "", "candidate does not include D5 head")
    adopted = adopted_root()
    for commit in (ADOPTED_MAIN, D1, D3, W3C, GEOGRAPHY):
        git(adopted, "cat-file", "-e", f"{commit}^{{commit}}")
    require(contained(adopted, W3C, ADOPTED_MAIN) and contained(adopted, GEOGRAPHY, ADOPTED_MAIN), "adopted-main contained-source evidence drift")
    require(not contained(adopted, D1, ADOPTED_MAIN) and not contained(adopted, D3, ADOPTED_MAIN), "reviewed blocker was incorrectly contained by adopted main")
    digests: dict[str, str] = {}
    for item in plan["controllingArtifacts"]:
        path, expected = item.get("path"), item.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), "control artifact shape drift")
        actual = sha256(ROOT / path)
        require(actual == expected, f"controlling artifact digest drift: {path}")
        digests[path] = actual
    return digests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("candidate", "released"), default="candidate")
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    require(args.mode == "candidate" and not args.require_tag, "rc.6 source candidate is not a released/taggable verifier mode")
    plan = read_json(ROOT / "versions/v1.0.0-rc.6/finalization.json")
    validate(plan)
    digests = validate_runtime(plan)
    if args.self_test:
        altered = dict(plan)
        altered["candidateState"] = "RELEASED"
        try:
            validate(altered)
        except ValueError:
            pass
        else:
            raise ValueError("finalization self-test accepted an invalid candidate state")
    identity = {"releaseVersion": plan["releaseVersion"], "requiredTag": plan["requiredTag"], "head": git(ROOT, "rev-parse", "HEAD"), "tree": git(ROOT, "rev-parse", "HEAD^{tree}"), "controls": digests}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print(f"[successor-release-finalization] OK (candidate; simulatedCandidateIdentity=sha256:{digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
