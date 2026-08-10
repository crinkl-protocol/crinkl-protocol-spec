#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protocol_version_const(schema: dict[str, Any]) -> str | None:
    return (
        (((schema.get("$defs") or {}).get("protocol") or {}).get("properties") or {})
        .get("protocolVersion", {})
        .get("const")
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    profile_root = (
        repo_root
        / "conformance"
        / "profiles"
        / "campaign-direct-buyer-reward-v1"
    )
    manifest = read_json(profile_root / "manifest.json")
    release_manifest = read_json(repo_root / "versions" / "release.json")
    release_status = str(release_manifest.get("status") or "")
    if release_status not in {"RELEASE_CANDIDATE_NOT_PUBLISHED", "RELEASED"}:
        raise ValueError("public release manifest status drift")
    is_released = release_status == "RELEASED"

    expected_profile_maturity = "released" if is_released else "release-candidate"
    if manifest.get("maturity") != expected_profile_maturity:
        raise ValueError("profile package maturity does not match release status")
    if manifest.get("releasedConformance") is not is_released:
        raise ValueError("profile releasedConformance does not match release status")
    if manifest.get("protocolObjectVersion") != "1.0.0-rc.1":
        raise ValueError("profile protocol object version drift")
    if manifest.get("publicRepositoryVersion") != "1.0.0-rc.3":
        raise ValueError("profile public repository version drift")
    if (manifest.get("engineeringSource") or {}).get("commit") != (
        "8c641f57201c75bac12819a0f903ae6105c7f3c3"
    ):
        raise ValueError("profile engineering source commit drift")
    expected_engineering_maturity = (
        "engineering-adopted-on-protected-main"
        if is_released
        else "engineering-candidate-not-merged-or-released"
    )
    if (manifest.get("engineeringSource") or {}).get("maturity") != (
        expected_engineering_maturity
    ):
        raise ValueError("profile engineering maturity does not match release status")

    artifacts = list(manifest.get("artifacts") or [])
    artifact_files = [str(artifact.get("file")) for artifact in artifacts]
    if len(artifacts) != 6 or len(set(artifact_files)) != len(artifact_files):
        raise ValueError("profile package must contain six unique byte-pinned artifacts")

    for artifact in artifacts:
        path = (profile_root / str(artifact["file"])).resolve()
        if profile_root.resolve() not in path.parents:
            raise ValueError(f"profile artifact escapes package: {artifact['file']}")
        if not path.is_file():
            raise ValueError(f"missing profile artifact: {artifact['file']}")
        actual = sha256_file(path)
        if actual != artifact.get("sha256"):
            raise ValueError(
                f"profile artifact hash mismatch: {artifact['file']} "
                f"actual={actual} expected={artifact.get('sha256')}"
            )

    if release_manifest != {
        "releaseVersion": "1.0.0-rc.3",
        "status": release_status,
        "requiredTag": "v1.0.0-rc.3",
        "defaultBindingProtocolVersion": "1.0.0-rc.2",
        "supportedWireProtocolVersions": ["1.0.0-rc.1", "1.0.0-rc.2"],
        "conformance": {
            "suite": "crinkl-protocol-conformance",
            "suiteVersion": 2,
            "manifest": "conformance/vectors/v1/manifest.json",
        },
        "releaseAuthority": {
            "acceptedReleaseIdentity": "AUTHORITY_ACCEPTED_TAG_AND_RELEASE_MANIFEST_DIGEST",
            "sourceBranchAuthority": "PROHIBITED",
        },
        "profiles": [
            {
                "kind": "campaign.directBuyerReward.profileV1",
                "maturity": "RELEASED" if is_released else "RELEASE_CANDIDATE",
                "runtimeAvailability": "UNAVAILABLE",
            }
        ],
    }:
        raise ValueError("public release manifest drift")

    conformance_manifest = read_json(
        repo_root / "conformance" / "vectors" / "v1" / "manifest.json"
    )
    if conformance_manifest.get("protocolVersion") != "1.0.0-rc.2":
        raise ValueError("default binding wire protocol version drift")
    if conformance_manifest.get("supportedWireProtocolVersions") != [
        "1.0.0-rc.1",
        "1.0.0-rc.2",
    ]:
        raise ValueError("supported wire protocol version set drift")
    if conformance_manifest.get("suiteVersion") != 2:
        raise ValueError("conformance suite version must be 2")
    if conformance_manifest.get("releaseVersion") != "1.0.0-rc.3":
        raise ValueError("conformance release version must be 1.0.0-rc.3")
    if conformance_manifest.get("releaseStatus") != release_status:
        raise ValueError("conformance manifest release status drift")

    expected_entry = dict(manifest.get("conformanceManifestEntry") or {})
    expected_entry_status = (
        "PRESENT_IN_RELEASED_RC3_SUITE_2"
        if is_released
        else "PRESENT_IN_RC3_SUITE_2_SOURCE_CANDIDATE"
    )
    if expected_entry.get("status") != expected_entry_status:
        raise ValueError("profile package conformance entry status drift")
    actual_entries = [
        entry
        for entry in conformance_manifest.get("vectors") or []
        if entry.get("kind") == "campaign.directBuyerReward.profileV1"
    ]
    if len(actual_entries) != 1:
        raise ValueError("conformance manifest must contain exactly one profile entry")
    expected_vector_entry = dict(expected_entry)
    expected_vector_entry.pop("status", None)
    if actual_entries[0] != expected_vector_entry:
        raise ValueError("profile package and conformance manifest entry mismatch")

    legacy_epoch = read_json(
        repo_root / "schemas" / "experimental" / "campaign-epoch.v1.schema.json"
    )
    legacy_epoch_path = (
        repo_root / "schemas" / "experimental" / "campaign-epoch.v1.schema.json"
    )
    candidate_epoch_path = (
        profile_root / "protocol" / "schemas" / "campaign_epoch_v1.schema.json"
    )
    candidate_epoch = read_json(candidate_epoch_path)
    reconciliation = read_json(
        profile_root
        / "conformance"
        / "v1"
        / "campaign.directBuyerReward.releaseReconciliationV1.json"
    )
    if reconciliation.get("decisionStatus") != "FINAL_RECONCILIATION_DECISION":
        raise ValueError("release reconciliation decision status drift")
    if reconciliation.get("currentPublicRelease") != {
        "repositoryVersion": "1.0.0-rc.2",
        "conformanceSuiteVersion": 1,
    }:
        raise ValueError("release reconciliation current public release mismatch")
    if reconciliation.get("targetPublicRelease") != {
        "repositoryVersion": "1.0.0-rc.3",
        "conformanceSuiteVersion": 2,
        "profileKind": "campaign.directBuyerReward.profileV1",
    }:
        raise ValueError("release reconciliation target public release mismatch")
    if reconciliation.get("wireVersionDecision") != {
        "protocolVersion": "1.0.0-rc.1",
        "treatment": "PRESERVE_EXACT_SIGNED_OBJECT_BYTES",
        "publicReleaseVersionIsNotWireProtocolVersion": True,
    }:
        raise ValueError("release reconciliation wire-version decision mismatch")

    epoch_resolution = dict(reconciliation.get("campaignEpochResolution") or {})
    adopted = dict(epoch_resolution.get("requiredAdoptedEngineeringSchema") or {})
    legacy = dict(epoch_resolution.get("legacyPublicExperimentalSchema") or {})
    if epoch_resolution.get("resolutionRule") != "EXACT_SCHEMA_ID_AND_SHA256":
        raise ValueError("Campaign Epoch resolution must use exact schema ID and SHA-256")
    if epoch_resolution.get("titleOnlyResolution") != "PROHIBITED":
        raise ValueError("Campaign Epoch title-only resolution must remain prohibited")
    if adopted.get("schemaId") != candidate_epoch.get("$id"):
        raise ValueError("adopted Epoch reconciliation schema ID mismatch")
    if adopted.get("sha256") != sha256_file(candidate_epoch_path):
        raise ValueError("adopted Epoch reconciliation hash mismatch")
    if legacy.get("schemaId") != legacy_epoch.get("$id"):
        raise ValueError("legacy Epoch reconciliation schema ID mismatch")
    if legacy.get("sha256") != sha256_file(legacy_epoch_path):
        raise ValueError("legacy Epoch immutable bytes changed")
    if adopted.get("schemaId") == legacy.get("schemaId"):
        raise ValueError("legacy and adopted Epoch schema IDs must stay distinct")
    if adopted.get("title") != candidate_epoch.get("title"):
        raise ValueError("adopted Epoch reconciliation title mismatch")
    if legacy.get("title") != legacy_epoch.get("title"):
        raise ValueError("legacy Epoch reconciliation title mismatch")
    if candidate_epoch.get("title") != legacy_epoch.get("title"):
        raise ValueError("fixture no longer exercises the title collision")
    if legacy.get("disposition") != (
        "PRESERVE_IMMUTABLE_EXPERIMENTAL_BYTES_EXCLUDE_FROM_PROFILE"
    ):
        raise ValueError("legacy Epoch disposition drift")

    if reconciliation.get("promotionRequirements") != [
        "ENGINEERING_CANDIDATE_MERGED_AND_RELEASED",
        "BYTE_IDENTICAL_PUBLIC_ARTIFACTS",
        "PUBLIC_RELEASE_VERSION_1_0_0_RC_3",
        "RELEASED_CONFORMANCE_SUITE_VERSION_2",
        "PROFILE_PRESENT_IN_RELEASED_MANIFEST_AND_VERIFIER",
        "LEGACY_EPOCH_RESOLUTION_ENFORCED_BY_SCHEMA_ID_AND_SHA256",
    ]:
        raise ValueError("release promotion requirements drift")
    if reconciliation.get("launchRequirements") != [
        "EXACT_RELEASED_PROFILE_ACCEPTED",
        "CAMPAIGN_RUNTIME_PROFILE_AVAILABLE",
        "DISTRIBUTED_VALIDATOR_ADMISSION_PROFILE_AVAILABLE",
    ]:
        raise ValueError("launch requirements drift")

    wire_version = reconciliation["wireVersionDecision"]["protocolVersion"]
    for relative in (
        "protocol/schemas/campaign_direct_buyer_reward_policy_v1.schema.json",
        "protocol/schemas/campaign_epoch_v1.schema.json",
    ):
        if protocol_version_const(read_json(profile_root / relative)) != wire_version:
            raise ValueError(f"wire protocol version mismatch: {relative}")

    if reconciliation.get("compilerGate") != {
        "status": "BLOCKED_UNTIL_EXACT_RELEASED_PROFILE",
        "requiredPublicRelease": "1.0.0-rc.3",
        "requiredConformanceSuiteVersion": 2,
        "requiredProfileKind": "campaign.directBuyerReward.profileV1",
        "publicationDraftAccepted": False,
    }:
        raise ValueError("compiler gate drift")

    if reconciliation.get("releaseAuthentication") != {
        "requiredTag": "v1.0.0-rc.3",
        "requiredReleaseManifestStatus": "RELEASED",
        "acceptedReleaseIdentity": "AUTHORITY_ACCEPTED_TAG_AND_RELEASE_MANIFEST_DIGEST",
        "sourceBranchAuthority": "PROHIBITED",
    }:
        raise ValueError("release authentication gate drift")

    expected_blockers = set()
    if not is_released:
        expected_blockers = {
            "ENGINEERING_CANDIDATE_NOT_MERGED_OR_RELEASED",
            "PUBLIC_RC3_SOURCE_CANDIDATE_NOT_PUBLISHED",
            "RELEASE_MANIFEST_STATUS_NOT_RELEASED",
        }
    if set(manifest.get("publicationBlockers") or []) != expected_blockers:
        raise ValueError("publication blockers do not match the reconciled release state")
    if manifest.get("launchBlockers") != [
        "RUNTIME_AND_DISTRIBUTED_VALIDATOR_PROFILE_UNAVAILABLE"
    ]:
        raise ValueError("launch blockers drift")

    print(
        "[campaign-direct-reward-release-profile] OK "
        f"({len(artifacts)} byte-pinned artifacts; "
        f"rc.3/suite-2 status={release_status})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
