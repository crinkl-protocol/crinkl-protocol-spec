#!/usr/bin/env python3
"""Hostile tests for the release-registry gate."""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
from pathlib import Path

import check_release_registry as checker


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hostile release-registry gate tests.")
    parser.add_argument(
        "--adopted-repo",
        type=Path,
        default=os.environ.get("CRINKL_PROTOCOL_ADOPTED_REPO") or None,
        help="Git checkout containing every pinned crinkl-protocol commit.",
    )
    args = parser.parse_args()
    if args.adopted_repo is None:
        parser.error("--adopted-repo or CRINKL_PROTOCOL_ADOPTED_REPO is required")
    return args


def assert_rejected(
    name: str,
    registry: dict,
    adopted_root: Path,
    release_manifest: dict | None = None,
) -> None:
    errors = checker.validate_registry(
        ROOT,
        load("versions/release-ledger.schema.json"),
        registry,
        release_manifest if release_manifest is not None else load("versions/release.json"),
        adopted_root,
    )
    if not errors:
        raise AssertionError(f"{name}: registry mutation was accepted")
    print(f"[release-registry-test] rejected: {name}")


def main() -> int:
    args = parse_args()
    adopted_root = args.adopted_repo.resolve()
    schema = load("versions/release-ledger.schema.json")
    registry = load("versions/release-registry.json")
    release_manifest = load("versions/release.json")
    valid_errors = checker.validate_registry(ROOT, schema, registry, release_manifest, adopted_root)
    if valid_errors:
        raise AssertionError(f"valid registry rejected: {valid_errors}")
    print(f"[release-registry-test] accepted: current registry (adopted repo: {adopted_root})")

    mutated = copy.deepcopy(registry)
    mutated["latestReleasedVersion"] = "1.0.0-rc.99"
    assert_rejected("dangling latest release", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["latestReleasedVersion"] = "1.0.0-rc.3"
    assert_rejected("stale latest release", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["reviewedCandidateVersion"] = "1.0.0-rc.99"
    assert_rejected("dangling reviewed candidate", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.6"] = copy.deepcopy(mutated["releases"]["1.0.0-rc.5"])
    mutated["releases"]["1.0.0-rc.6"]["plannedTag"] = "v1.0.0-rc.6"
    mutated["releases"]["1.0.0-rc.6"]["previousRelease"] = "1.0.0-rc.5"
    assert_rejected("stale reviewed candidate", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.5"]["previousRelease"] = "1.0.0-rc.99"
    assert_rejected("dangling predecessor", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.1"]["previousRelease"] = "1.0.0-rc.5"
    assert_rejected("predecessor cycle", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["actualTag"] = "v1.0.0-rc.4"
    assert_rejected("tag-key mismatch", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.5"]["actualTag"] = "v1.0.0-rc.5"
    assert_rejected("unpublished candidate actual tag", mutated, adopted_root)

    original_tag_ref_exists = checker.tag_ref_exists
    try:
        checker.tag_ref_exists = lambda root, tag: tag == "v1.0.0-rc.5" or original_tag_ref_exists(root, tag)
        assert_rejected("unpublished candidate planned tag ref", copy.deepcopy(registry), adopted_root)
    finally:
        checker.tag_ref_exists = original_tag_ref_exists

    original_run = checker.subprocess.run
    def fail_tag_lookup(command, *args, **kwargs):
        if len(command) > 3 and command[3] == "show-ref":
            return subprocess.CompletedProcess(command, 128, b"", b"simulated tag lookup failure")
        return original_run(command, *args, **kwargs)

    try:
        checker.subprocess.run = fail_tag_lookup
        try:
            checker.tag_ref_exists(ROOT, "v1.0.0-rc.5")
        except ValueError as exc:
            if "simulated tag lookup failure" not in str(exc):
                raise AssertionError(f"unexpected tag lookup failure: {exc}") from exc
        else:
            raise AssertionError("tag lookup failure was treated as an absent ref")
        errors = checker.validate_registry(ROOT, schema, copy.deepcopy(registry), release_manifest, adopted_root)
        if not any("simulated tag lookup failure" in item for item in errors):
            raise AssertionError(f"tag lookup failure was not reported by registry validation: {errors}")
        print("[release-registry-test] rejected: tag lookup failure")
    finally:
        checker.subprocess.run = original_run

    with tempfile.TemporaryDirectory() as directory:
        duplicate = Path(directory) / "duplicate.json"
        duplicate.write_text('{"duplicate": 1, "duplicate": 2}', encoding="utf-8")
        try:
            checker.load_json(duplicate)
        except ValueError:
            print("[release-registry-test] rejected: duplicate JSON key")
        else:
            raise AssertionError("duplicate JSON key was accepted")

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["artifactInventory"][0]["digest"] = "sha256:" + "0" * 64
    assert_rejected("artifact digest mismatch", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["authority"]["releaseAuthority"] = "REVIEWED_SOURCE_NOT_RELEASED"
    assert_rejected("released authority tuple", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["campaign.directBuyerReward.profileV1"]["maturity"] = "CANDIDATE"
    assert_rejected("profile maturity authority", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["source"]["tree"] = "0" * 40
    assert_rejected("source tree mismatch", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["adoptedSources"][0]["commit"] = "f" * 40
    assert_rejected("fabricated release adopted commit", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["campaign.directBuyerReward.profileV1"]["adoptedSource"]["commit"] = "f" * 40
    assert_rejected("fabricated profile adopted commit", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["campaign.directBuyerReward.profileV1"]["runtimeSupport"] = "AVAILABLE"
    assert_rejected("runtime activation claim", mutated, adopted_root)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["token.spendAttestation.holderBinding.v2"]["objectConstraints"][0]["requiredSchemaVersions"] = [3]
    assert_rejected("required schema version not supported", mutated, adopted_root)

    reused = copy.deepcopy(registry)
    reused["profiles"]["portable.spendAttestation.reuse.v1"] = copy.deepcopy(
        reused["profiles"]["token.spendAttestation.holderBinding.v2"]
    )
    if checker.validate_registry(ROOT, schema, reused, release_manifest, adopted_root):
        raise AssertionError("object identifier reuse across profiles was rejected")
    print("[release-registry-test] accepted: object identifier reuse across profiles")

    mutated = copy.deepcopy(registry)
    constraint = copy.deepcopy(mutated["profiles"]["token.spendAttestation.holderBinding.v2"]["objectConstraints"][0])
    mutated["profiles"]["token.spendAttestation.holderBinding.v2"]["objectConstraints"].append(constraint)
    assert_rejected("duplicate object identifier within profile", mutated, adopted_root)

    manifest = copy.deepcopy(release_manifest)
    manifest["profiles"][0]["kind"] = "unregistered.profile.v1"
    assert_rejected("unregistered release manifest profile", copy.deepcopy(registry), adopted_root, manifest)

    manifest = copy.deepcopy(release_manifest)
    manifest["profiles"].append(copy.deepcopy(manifest["profiles"][0]))
    assert_rejected("duplicate release manifest profile kind", copy.deepcopy(registry), adopted_root, manifest)

    mutated = copy.deepcopy(registry)
    mutated["releasedSchemaIdentityCollisionReceipt"]["digest"] = "sha256:" + "f" * 64
    assert_rejected("collision receipt mutation", mutated, adopted_root)

    baseline = copy.deepcopy(registry)
    deleted = copy.deepcopy(registry)
    del deleted["profiles"]["campaign.directBuyerReward.profileV1"]
    if not checker.validate_baseline(deleted, baseline):
        raise AssertionError("baseline profile deletion was accepted")
    print("[release-registry-test] rejected: baseline deletion")

    changed = copy.deepcopy(registry)
    changed["embeddedWireVersionObservations"]["1.0.0-rc.2"]["classification"] = "MUTATED"
    if not checker.validate_baseline(changed, baseline):
        raise AssertionError("baseline wire observation mutation was accepted")
    print("[release-registry-test] rejected: baseline mutation")

    appended = copy.deepcopy(registry)
    appended["additionalCollisionObservations"].append(
        {"algorithm": "sha256", "digest": "sha256:" + "a" * 64, "state": "OBSERVED_UNRESOLVED"}
    )
    if checker.validate_baseline(appended, baseline):
        raise AssertionError("baseline rejected an allowed append")
    print("[release-registry-test] accepted: baseline append")

    heads_appended = copy.deepcopy(registry)
    heads_appended["unassignedSourceHeads"].append(copy.deepcopy(heads_appended["unassignedSourceHeads"][0]))
    if checker.validate_baseline(heads_appended, baseline):
        raise AssertionError("baseline rejected an allowed unassigned-source suffix append")
    print("[release-registry-test] accepted: unassigned source append")

    observation_baseline = copy.deepcopy(registry)
    observation_baseline["additionalCollisionObservations"] = [
        {"algorithm": "sha256", "digest": "sha256:" + "b" * 64, "state": "OBSERVED_UNRESOLVED"},
        {"algorithm": "sha256", "digest": "sha256:" + "c" * 64, "state": "OBSERVED_UNRESOLVED"},
    ]
    changed = copy.deepcopy(observation_baseline)
    changed["additionalCollisionObservations"].reverse()
    if not checker.validate_baseline(changed, observation_baseline):
        raise AssertionError("baseline observation reorder was accepted")
    print("[release-registry-test] rejected: observation reorder")

    changed = copy.deepcopy(registry)
    changed["unassignedSourceHeads"][0]["state"] = "MUTATED"
    if not checker.validate_baseline(changed, baseline):
        raise AssertionError("baseline unassigned source mutation was accepted")
    print("[release-registry-test] rejected: unassigned source mutation")

    changed = copy.deepcopy(registry)
    changed["ledgerVersion"] = 2
    if not checker.validate_baseline(changed, baseline):
        raise AssertionError("baseline ledger version mutation was accepted")
    print("[release-registry-test] rejected: ledger version mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
