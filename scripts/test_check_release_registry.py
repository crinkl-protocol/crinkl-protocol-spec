#!/usr/bin/env python3
"""Hostile tests for the release-registry gate."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import check_release_registry as checker


ROOT = Path(__file__).resolve().parents[1]
ADOPTED_ROOT = Path("/home/azureuser/crinkl-protocol")


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def assert_rejected(name: str, registry: dict, release_manifest: dict | None = None) -> None:
    errors = checker.validate_registry(
        ROOT,
        load("versions/release-ledger.schema.json"),
        registry,
        release_manifest if release_manifest is not None else load("versions/release.json"),
        ADOPTED_ROOT,
    )
    if not errors:
        raise AssertionError(f"{name}: registry mutation was accepted")
    print(f"[release-registry-test] rejected: {name}")


def main() -> int:
    schema = load("versions/release-ledger.schema.json")
    registry = load("versions/release-registry.json")
    release_manifest = load("versions/release.json")
    valid_errors = checker.validate_registry(ROOT, schema, registry, release_manifest, ADOPTED_ROOT)
    if valid_errors:
        raise AssertionError(f"valid registry rejected: {valid_errors}")
    print("[release-registry-test] accepted: current registry")

    mutated = copy.deepcopy(registry)
    mutated["latestReleasedVersion"] = "1.0.0-rc.99"
    assert_rejected("dangling latest release", mutated)

    mutated = copy.deepcopy(registry)
    mutated["latestReleasedVersion"] = "1.0.0-rc.3"
    assert_rejected("stale latest release", mutated)

    mutated = copy.deepcopy(registry)
    mutated["reviewedCandidateVersion"] = "1.0.0-rc.99"
    assert_rejected("dangling reviewed candidate", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.6"] = copy.deepcopy(mutated["releases"]["1.0.0-rc.5"])
    mutated["releases"]["1.0.0-rc.6"]["plannedTag"] = "v1.0.0-rc.6"
    mutated["releases"]["1.0.0-rc.6"]["previousRelease"] = "1.0.0-rc.5"
    assert_rejected("stale reviewed candidate", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.5"]["previousRelease"] = "1.0.0-rc.99"
    assert_rejected("dangling predecessor", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.1"]["previousRelease"] = "1.0.0-rc.5"
    assert_rejected("predecessor cycle", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["actualTag"] = "v1.0.0-rc.4"
    assert_rejected("tag-key mismatch", mutated)

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
    assert_rejected("artifact digest mismatch", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["authority"]["releaseAuthority"] = "REVIEWED_SOURCE_NOT_RELEASED"
    assert_rejected("released authority tuple", mutated)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["campaign.directBuyerReward.profileV1"]["maturity"] = "CANDIDATE"
    assert_rejected("profile maturity authority", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["source"]["tree"] = "0" * 40
    assert_rejected("source tree mismatch", mutated)

    mutated = copy.deepcopy(registry)
    mutated["releases"]["1.0.0-rc.3"]["adoptedSources"][0]["commit"] = "f" * 40
    assert_rejected("fabricated release adopted commit", mutated)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["campaign.directBuyerReward.profileV1"]["adoptedSource"]["commit"] = "f" * 40
    assert_rejected("fabricated profile adopted commit", mutated)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["campaign.directBuyerReward.profileV1"]["runtimeSupport"] = "AVAILABLE"
    assert_rejected("runtime activation claim", mutated)

    mutated = copy.deepcopy(registry)
    mutated["profiles"]["token.spendAttestation.holderBinding.v2"]["objectConstraints"][0]["requiredSchemaVersions"] = [3]
    assert_rejected("required schema version not supported", mutated)

    reused = copy.deepcopy(registry)
    reused["profiles"]["portable.spendAttestation.reuse.v1"] = copy.deepcopy(
        reused["profiles"]["token.spendAttestation.holderBinding.v2"]
    )
    if checker.validate_registry(ROOT, schema, reused, release_manifest, ADOPTED_ROOT):
        raise AssertionError("object identifier reuse across profiles was rejected")
    print("[release-registry-test] accepted: object identifier reuse across profiles")

    mutated = copy.deepcopy(registry)
    constraint = copy.deepcopy(mutated["profiles"]["token.spendAttestation.holderBinding.v2"]["objectConstraints"][0])
    mutated["profiles"]["token.spendAttestation.holderBinding.v2"]["objectConstraints"].append(constraint)
    assert_rejected("duplicate object identifier within profile", mutated)

    manifest = copy.deepcopy(release_manifest)
    manifest["profiles"][0]["kind"] = "unregistered.profile.v1"
    assert_rejected("unregistered release manifest profile", copy.deepcopy(registry), manifest)

    manifest = copy.deepcopy(release_manifest)
    manifest["profiles"].append(copy.deepcopy(manifest["profiles"][0]))
    assert_rejected("duplicate release manifest profile kind", copy.deepcopy(registry), manifest)

    mutated = copy.deepcopy(registry)
    mutated["releasedSchemaIdentityCollisionReceipt"]["digest"] = "sha256:" + "f" * 64
    assert_rejected("collision receipt mutation", mutated)

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
