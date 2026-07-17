#!/usr/bin/env python3
from __future__ import annotations

import base64
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonicalize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_release_reconciliation(repo_root: Path) -> None:
    reconciliation = read_json(
        repo_root
        / "conformance"
        / "v1"
        / "campaign.directBuyerReward.releaseReconciliationV1.json"
    )
    if reconciliation.get("decisionStatus") != "FINAL_RECONCILIATION_DECISION":
        raise ValueError("release reconciliation decision status drift")

    current = dict(reconciliation.get("currentPublicRelease") or {})
    target = dict(reconciliation.get("targetPublicRelease") or {})
    if current != {
        "repositoryVersion": "1.0.0-rc.2",
        "conformanceSuiteVersion": 1,
    }:
        raise ValueError("release reconciliation current public release drift")
    if target != {
        "repositoryVersion": "1.0.0-rc.3",
        "conformanceSuiteVersion": 2,
        "profileKind": "campaign.directBuyerReward.profileV1",
    }:
        raise ValueError("release reconciliation target public release drift")

    wire = dict(reconciliation.get("wireVersionDecision") or {})
    if wire != {
        "protocolVersion": "1.0.0-rc.1",
        "treatment": "PRESERVE_EXACT_SIGNED_OBJECT_BYTES",
        "publicReleaseVersionIsNotWireProtocolVersion": True,
    }:
        raise ValueError("release reconciliation wire-version decision drift")

    epoch_resolution = dict(reconciliation.get("campaignEpochResolution") or {})
    if epoch_resolution.get("resolutionRule") != "EXACT_SCHEMA_ID_AND_SHA256":
        raise ValueError("Campaign Epoch must resolve by exact schema ID and SHA-256")
    if epoch_resolution.get("titleOnlyResolution") != "PROHIBITED":
        raise ValueError("Campaign Epoch title-only resolution must remain prohibited")

    required_epoch = dict(
        epoch_resolution.get("requiredAdoptedEngineeringSchema") or {}
    )
    epoch_path = repo_root / "protocol" / "schemas" / "campaign_epoch_v1.schema.json"
    epoch_schema = read_json(epoch_path)
    if required_epoch.get("schemaId") != epoch_schema.get("$id"):
        raise ValueError("release reconciliation adopted Epoch schema ID mismatch")
    if required_epoch.get("sha256") != sha256_file(epoch_path):
        raise ValueError("release reconciliation adopted Epoch hash mismatch")
    if required_epoch.get("profileUse") != "REQUIRED":
        raise ValueError("adopted engineering Epoch must remain required by the profile")

    legacy_epoch = dict(epoch_resolution.get("legacyPublicExperimentalSchema") or {})
    if legacy_epoch != {
        "schemaId": "crinkl://protocol/schemas/experimental/campaign-epoch.v1",
        "title": "CampaignEpochV1",
        "sha256": "603c6828d90e0e0d4e8f1c1bb5fdb7d24ff580ada7dcea3e052836ea00884a3d",
        "disposition": "PRESERVE_IMMUTABLE_EXPERIMENTAL_BYTES_EXCLUDE_FROM_PROFILE",
    }:
        raise ValueError("release reconciliation legacy Epoch decision drift")
    if legacy_epoch["schemaId"] == required_epoch.get("schemaId"):
        raise ValueError("legacy and adopted Epoch schema IDs must remain distinct")

    if reconciliation.get("promotionRequirements") != [
        "ENGINEERING_CANDIDATE_MERGED_AND_RELEASED",
        "BYTE_IDENTICAL_PUBLIC_ARTIFACTS",
        "PUBLIC_RELEASE_VERSION_1_0_0_RC_3",
        "RELEASED_CONFORMANCE_SUITE_VERSION_2",
        "PROFILE_PRESENT_IN_RELEASED_MANIFEST_AND_VERIFIER",
        "LEGACY_EPOCH_RESOLUTION_ENFORCED_BY_SCHEMA_ID_AND_SHA256",
    ]:
        raise ValueError("release reconciliation promotion requirements drift")
    if reconciliation.get("launchRequirements") != [
        "EXACT_RELEASED_PROFILE_ACCEPTED",
        "CAMPAIGN_RUNTIME_PROFILE_AVAILABLE",
        "DISTRIBUTED_VALIDATOR_ADMISSION_PROFILE_AVAILABLE",
    ]:
        raise ValueError("release reconciliation launch requirements drift")

    compiler_gate = dict(reconciliation.get("compilerGate") or {})
    if compiler_gate != {
        "status": "BLOCKED_UNTIL_EXACT_RELEASED_PROFILE",
        "requiredPublicRelease": "1.0.0-rc.3",
        "requiredConformanceSuiteVersion": 2,
        "requiredProfileKind": "campaign.directBuyerReward.profileV1",
        "publicationDraftAccepted": False,
    }:
        raise ValueError("release reconciliation compiler gate drift")

    release_authentication = dict(reconciliation.get("releaseAuthentication") or {})
    if release_authentication != {
        "requiredTag": "v1.0.0-rc.3",
        "requiredReleaseManifestStatus": "RELEASED",
        "acceptedReleaseIdentity": "AUTHORITY_ACCEPTED_TAG_AND_RELEASE_MANIFEST_DIGEST",
        "sourceBranchAuthority": "PROHIBITED",
    }:
        raise ValueError("release reconciliation authentication gate drift")


def unsigned(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop("signatures", None)
    return result


def artifact_ref(value: dict[str, Any]) -> str:
    return "sha256:" + str(value["signatures"]["tokenHash"])


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc
    )


def verify_signed(value: dict[str, Any], prefix: str) -> str | None:
    signature = dict(value.get("signatures") or {})
    actual_hash = sha256_hex(canonicalize(unsigned(value)))
    if signature.get("tokenHash") != actual_hash:
        return f"{prefix}_TOKEN_HASH_MISMATCH"
    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(str(signature["publicKey"]), validate=True)
        )
        public_key.verify(
            base64.b64decode(str(signature["signature"]), validate=True),
            bytes.fromhex(actual_hash),
        )
    except (InvalidSignature, ValueError, KeyError):
        return f"{prefix}_SIGNATURE_INVALID"
    return None


def standalone_reward_policy_reject(
    policy: dict[str, Any],
    policy_validator: Draft202012Validator,
) -> str | None:
    if list(policy_validator.iter_errors(policy)):
        return "REWARD_POLICY_SCHEMA_REJECT"
    policy_signature_reject = verify_signed(policy, "REWARD_POLICY")
    if policy_signature_reject:
        return policy_signature_reject
    return None


def reward_policy_reject(
    policy: dict[str, Any],
    epoch: dict[str, Any],
    policy_validator: Draft202012Validator,
    epoch_validator: Draft202012Validator,
) -> str | None:
    policy_reject = standalone_reward_policy_reject(policy, policy_validator)
    if policy_reject:
        return policy_reject
    if list(epoch_validator.iter_errors(epoch)):
        return "CAMPAIGN_EPOCH_SCHEMA_REJECT"
    epoch_signature_reject = verify_signed(epoch, "CAMPAIGN_EPOCH")
    if epoch_signature_reject:
        return epoch_signature_reject
    if epoch.get("rewardPolicyRef") != artifact_ref(policy):
        return "CAMPAIGN_EPOCH_REWARD_POLICY_REF_MISMATCH"
    if not (
        parse_time(str(policy["issuedAt"]))
        <= parse_time(str(epoch["issuedAt"]))
        <= parse_time(str(epoch["effectiveFrom"]))
    ):
        return "REWARD_POLICY_TIME_ORDER"
    return None


def resolve_schema(
    vector_base: Path,
    vectors: dict[str, Any],
    field: str,
    expected: Path,
) -> dict[str, Any]:
    actual = (vector_base / str(vectors.get(field))).resolve()
    if actual != expected.resolve():
        raise ValueError(f"Campaign direct-buyer-reward vector {field} path mismatch")
    schema = read_json(actual)
    Draft202012Validator.check_schema(schema)
    return schema


def verify_campaign_direct_reward_profile_vectors(repo_root: Path) -> None:
    verify_release_reconciliation(repo_root)
    vector_path = (
        repo_root
        / "conformance"
        / "v1"
        / "vectors"
        / "campaign.directBuyerReward.profileV1.json"
    )
    vectors = read_json(vector_path)
    vector_base = vector_path.parent

    if vectors.get("kind") != "campaign.directBuyerReward.profileV1":
        raise ValueError("Campaign direct-buyer-reward vector kind mismatch")

    policy_schema = resolve_schema(
        vector_base,
        vectors,
        "rewardPolicySchema",
        repo_root
        / "protocol"
        / "schemas"
        / "campaign_direct_buyer_reward_policy_v1.schema.json",
    )
    epoch_schema = resolve_schema(
        vector_base,
        vectors,
        "campaignEpochSchema",
        repo_root / "protocol" / "schemas" / "campaign_epoch_v1.schema.json",
    )
    policy_validator = Draft202012Validator(policy_schema)
    epoch_validator = Draft202012Validator(epoch_schema)

    primary_by_id: dict[str, dict[str, Any]] = {}
    protected_terms = ("sport drink", "raposa", "businessname", "productname", "sourceurl")

    for case in vectors.get("primaryCases") or []:
        case_id = str(case["id"])
        policy = dict(case["rewardPolicy"])
        epoch = dict(case["campaignEpoch"])
        policy_reject = reward_policy_reject(
            policy, epoch, policy_validator, epoch_validator
        )
        if policy_reject:
            raise ValueError(f"valid direct reward case {case_id} rejected: {policy_reject}")
        if artifact_ref(policy) != case.get("expectedRewardPolicyRef"):
            raise ValueError(f"reward policy ref mismatch: {case_id}")
        if canonicalize(unsigned(policy)) != case.get(
            "expectedUnsignedRewardPolicyCanonical"
        ):
            raise ValueError(f"reward policy canonical mismatch: {case_id}")
        if artifact_ref(epoch) != case.get("expectedCampaignEpochRef"):
            raise ValueError(f"Campaign Epoch ref mismatch: {case_id}")
        wire = "\n".join([canonicalize(policy), canonicalize(epoch)]).lower()
        for term in protected_terms:
            if term in wire:
                raise ValueError(f"protected term {term!r} leaked into wire case {case_id}")
        primary_by_id[case_id] = case

    if len(primary_by_id) != 2:
        raise ValueError("Direct buyer-reward conformance requires two primary cases")

    policy_shapes = {
        tuple(sorted(dict(case["rewardPolicy"]).keys()))
        for case in primary_by_id.values()
    }
    if len(policy_shapes) != 1:
        raise ValueError("business fixtures do not share one direct buyer-reward wire shape")

    for case in vectors.get("rejectCases") or []:
        base = primary_by_id[str(case["baseCaseId"])]
        artifact = str(case["artifact"])
        if artifact in ("REWARD_POLICY", "COMPOSITION"):
            actual = reward_policy_reject(
                dict(case["input"]),
                dict(case.get("campaignEpoch") or base["campaignEpoch"]),
                policy_validator,
                epoch_validator,
            )
        else:
            raise ValueError(f"unknown reject artifact kind: {artifact}")
        if actual != case.get("expectedRejectCode"):
            raise ValueError(
                f"direct buyer-reward reject mismatch {case['id']}: "
                f"actual={actual} expected={case.get('expectedRejectCode')}"
            )

    for case in vectors.get("equivocationCases") or []:
        base = primary_by_id[str(case["baseCaseId"])]
        first = dict(case["firstInput"])
        second = dict(case["secondInput"])
        kind = str(case["kind"])
        if kind == "REWARD_POLICY":
            first_reject = standalone_reward_policy_reject(first, policy_validator)
            second_reject = standalone_reward_policy_reject(second, policy_validator)
            same_position = (
                first["rewardPolicyAuthorityRef"] == second["rewardPolicyAuthorityRef"]
                and first["policyId"] == second["policyId"]
            )
            actual = (
                "REWARD_POLICY_EQUIVOCATION"
                if first_reject is None
                and second_reject is None
                and same_position
                and artifact_ref(first) != artifact_ref(second)
                else None
            )
        else:
            raise ValueError(f"unknown equivocation kind: {kind}")
        if actual != case.get("expectedRejectCode"):
            raise ValueError(
                f"equivocation mismatch {case['id']}: "
                f"actual={actual} expected={case.get('expectedRejectCode')}"
            )


if __name__ == "__main__":
    verify_campaign_direct_reward_profile_vectors(
        Path(__file__).resolve().parents[1]
    )
    print("[campaign-direct-buyer-reward-check] OK")
