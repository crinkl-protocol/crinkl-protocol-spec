#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


PROTOCOL_VERSION = "1.0.0-rc.1"
VECTOR_PATH = Path("conformance/v1/vectors/campaign.directBuyerReward.profileV1.json")


def canonicalize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def named_ref(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def unsigned(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop("signatures", None)
    return result


def raw_public_key(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def sign_artifact(
    artifact: dict[str, Any],
    private_key: Ed25519PrivateKey,
    issued_by: str,
    key_id: str,
) -> dict[str, Any]:
    result = unsigned(artifact)
    canonical = canonicalize(result)
    token_hash = sha256_hex(canonical)
    result["signatures"] = {
        "issuedBy": issued_by,
        "keyId": key_id,
        "publicKey": base64.b64encode(raw_public_key(private_key)).decode("ascii"),
        "tokenHash": token_hash,
        "signature": base64.b64encode(
            private_key.sign(bytes.fromhex(token_hash))
        ).decode("ascii"),
    }
    return result


def artifact_ref(value: dict[str, Any]) -> str:
    return "sha256:" + str(value["signatures"]["tokenHash"])


ALLOCATION_BOUNDARY = {
    "buyerRewardLegCount": 1,
    "promoterRewardLeg": "NONE",
    "referrerRewardLeg": "NONE",
    "splitRule": "NO_PROMOTER_OR_REFERRER_SPLIT",
}

ATTRIBUTION_BOUNDARY = {
    "qualifyingOutcomeSource": "CAMPAIGN_EPOCH_CONVERSION_DEFINITION",
    "campaignAttributionSource": "CAMPAIGN_EPOCH_ATTRIBUTION_POLICY",
    "affiliateLinkOrCouponUseRequired": False,
    "affiliateCommissionAffectsBuyerReward": False,
}

CLAIM_BOUNDARY = {
    "rewardRecipientRule": "EXACT_OUTCOME_BOUND_BUYER_RECIPIENT",
    "rewardClaimCeilingSource": "CAMPAIGN_EPOCH_MAXIMUM_CLAIM_LEVEL",
    "perConversionIncrementalityClaim": "PROHIBITED",
    "rewardEstablishesAffiliateCommission": False,
    "rewardEstablishesSettlement": False,
}

PRIVACY_BOUNDARY = {
    "protectedCommercialMetadata": "NOT_REQUIRED_IN_PUBLIC_ARTIFACT",
    "targetIdentityRule": "RESOLVE_EXACT_COMMITTED_REFERENCES",
    "stableBuyerIdentifier": "PROHIBITED",
}

def build_reward_policy(
    label: str,
    policy_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    policy = {
        "tokenType": "CAMPAIGN_DIRECT_BUYER_REWARD_POLICY",
        "schemaVersion": 1,
        "protocol": {"protocolVersion": PROTOCOL_VERSION},
        "policyId": f"direct-buyer-reward-{label}",
        "issuedAt": "2026-08-01T05:00:00.000Z",
        "mechanic": "DIRECT_BUYER_REWARD",
        "rewardTermsRef": named_ref(f"{label}:reward-terms"),
        "outcomeEvidenceProfileRef": named_ref(f"{label}:outcome-evidence-profile"),
        "allocationBoundary": copy.deepcopy(ALLOCATION_BOUNDARY),
        "attributionBoundary": copy.deepcopy(ATTRIBUTION_BOUNDARY),
        "claimBoundary": copy.deepcopy(CLAIM_BOUNDARY),
        "privacyBoundary": copy.deepcopy(PRIVACY_BOUNDARY),
        "rewardPolicyAuthorityRef": named_ref(f"{label}:reward-policy-authority"),
    }
    return sign_artifact(
        policy,
        policy_key,
        issued_by=f"reward-policy-authority-{label}",
        key_id=f"reward-policy-key-{label}",
    )


def build_epoch(
    label: str,
    campaign_id: str,
    reward_policy_ref: str,
    epoch_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    epoch = {
        "tokenType": "CAMPAIGN_EPOCH",
        "schemaVersion": 1,
        "protocol": {"protocolVersion": PROTOCOL_VERSION},
        "epochSeriesId": f"epoch-{campaign_id}",
        "epochVersion": 1,
        "previousEpochRef": None,
        "campaignNamespaceRef": named_ref("campaign-namespace:conformance"),
        "campaignId": campaign_id,
        "lockedAt": "2026-08-01T06:00:00.000Z",
        "effectiveFrom": "2026-08-02T00:00:00.000Z",
        "effectiveTo": "2026-09-01T00:00:00.000Z",
        "issuedAt": "2026-08-01T06:00:00.000Z",
        "preStateConditionRef": named_ref(f"{label}:pre-state-condition"),
        "targetMerchantSetRef": named_ref(f"{label}:target-merchant-set"),
        "timingPolicyRef": named_ref(f"{label}:timing-policy"),
        "eventPolicyRef": named_ref(f"{label}:event-policy"),
        "attributionPolicyRef": named_ref(f"{label}:attribution-policy"),
        "conversionDefinitionRef": named_ref(f"{label}:conversion-definition"),
        "rewardPolicyRef": reward_policy_ref,
        "fundingTermsRef": named_ref(f"{label}:funding-terms"),
        "settlementPolicyRef": named_ref(f"{label}:settlement-policy"),
        "allowedEventTypes": ["ENGAGEMENT"],
        "allowedExposureSurfaceRefs": [named_ref(f"{label}:exposure-surface")],
        "eventPublisherAuthorityRefs": [named_ref(f"{label}:event-authority")],
        "statusPublisherAuthorityRefs": [named_ref(f"{label}:status-authority")],
        "maximumClaimLevel": "ATTRIBUTED",
        "fundingEvidenceRule": "SEPARATELY_RESOLVED_IF_REQUIRED",
        "epochAuthorityRef": named_ref(f"{label}:epoch-authority"),
    }
    return sign_artifact(
        epoch,
        epoch_key,
        issued_by=f"epoch-authority-{label}",
        key_id=f"epoch-key-{label}",
    )


def resign(
    source: dict[str, Any],
    key: Ed25519PrivateKey,
    mutate: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    result = unsigned(source)
    mutate(result)
    return sign_artifact(
        result,
        key,
        issued_by=str(source["signatures"]["issuedBy"]),
        key_id=str(source["signatures"]["keyId"]),
    )


def primary_case(
    case_id: str,
    business_kind: str,
    label: str,
    campaign_id: str,
    policy_key: Ed25519PrivateKey,
    epoch_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    policy = build_reward_policy(label, policy_key)
    epoch = build_epoch(label, campaign_id, artifact_ref(policy), epoch_key)
    return {
        "id": case_id,
        "businessCase": {
            "kind": business_kind,
            "note": "Conformance metadata only; this value is not present in wire artifacts.",
        },
        "rewardPolicy": policy,
        "expectedRewardPolicyRef": artifact_ref(policy),
        "expectedUnsignedRewardPolicyCanonical": canonicalize(unsigned(policy)),
        "campaignEpoch": epoch,
        "expectedCampaignEpochRef": artifact_ref(epoch),
    }


def build_vectors() -> dict[str, Any]:
    policy_key_alpha = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("51" * 32))
    policy_key_beta = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("52" * 32))
    epoch_key_alpha = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("61" * 32))
    epoch_key_beta = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("62" * 32))

    product = primary_case(
        "operator_product_target",
        "AFFILIATE_OPERATOR_PRODUCT_TARGET",
        "alpha",
        "campaign-alpha",
        policy_key_alpha,
        epoch_key_alpha,
    )
    restaurant = primary_case(
        "operator_restaurant_target",
        "OPERATOR_RESTAURANT_TARGET",
        "beta",
        "campaign-beta",
        policy_key_beta,
        epoch_key_beta,
    )

    policy = product["rewardPolicy"]
    epoch = product["campaignEpoch"]

    changed_policy = copy.deepcopy(policy)
    changed_policy["rewardTermsRef"] = named_ref("changed-after-signing")

    invalid_policy_signature = copy.deepcopy(policy)
    signature = str(invalid_policy_signature["signatures"]["signature"])
    invalid_policy_signature["signatures"]["signature"] = (
        ("A" if signature[0] != "A" else "B") + signature[1:]
    )

    mismatched_epoch = resign(
        epoch,
        epoch_key_alpha,
        lambda value: value.__setitem__("rewardPolicyRef", named_ref("wrong-policy")),
    )

    late_policy = resign(
        policy,
        policy_key_alpha,
        lambda value: value.__setitem__("issuedAt", "2026-08-01T06:00:00.001Z"),
    )
    late_policy_epoch = resign(
        epoch,
        epoch_key_alpha,
        lambda value: value.__setitem__("rewardPolicyRef", artifact_ref(late_policy)),
    )

    alternate_policy = resign(
        policy,
        policy_key_alpha,
        lambda value: value.__setitem__("rewardTermsRef", named_ref("alternate-terms")),
    )
    return {
        "kind": "campaign.directBuyerReward.profileV1",
        "vectorVersion": 1,
        "protocolVersion": PROTOCOL_VERSION,
        "rewardPolicySchema": "../../../protocol/schemas/campaign_direct_buyer_reward_policy_v1.schema.json",
        "campaignEpochSchema": "../../../protocol/schemas/campaign_epoch_v1.schema.json",
        "status": "NORMATIVE_PROTOCOL_CONFORMANCE_RUNTIME_UNAVAILABLE",
        "wireNonClaims": [
            "NO_SPONSOR_OR_BRAND_ROLE_ASSUMPTION",
            "NO_AFFILIATE_COMMISSION_OR_LINK_USE_PREREQUISITE",
            "NO_PRODUCT_OR_LINE_ITEM_PURCHASE_PROOF",
            "NO_PER_CONVERSION_INCREMENTALITY",
            "NO_FUNDING_DEPOSIT_ESCROW_SETTLEMENT_OR_REFUND_EFFECT",
            "NO_VALIDATOR_NETWORK_FINALITY",
            "NO_RUNTIME_OR_DEPLOYMENT_CLAIM",
        ],
        "primaryCases": [product, restaurant],
        "rejectCases": [
            {
                "id": "sponsor_field_not_part_of_direct_policy",
                "baseCaseId": product["id"],
                "artifact": "REWARD_POLICY",
                "input": resign(policy, policy_key_alpha, lambda value: value.__setitem__("sponsorId", "party-1")),
                "expectedRejectCode": "REWARD_POLICY_SCHEMA_REJECT",
            },
            {
                "id": "affiliate_link_use_cannot_gate_reward",
                "baseCaseId": product["id"],
                "artifact": "REWARD_POLICY",
                "input": resign(policy, policy_key_alpha, lambda value: value["attributionBoundary"].__setitem__("affiliateLinkOrCouponUseRequired", True)),
                "expectedRejectCode": "REWARD_POLICY_SCHEMA_REJECT",
            },
            {
                "id": "promoter_leg_not_direct_reward",
                "baseCaseId": product["id"],
                "artifact": "REWARD_POLICY",
                "input": resign(policy, policy_key_alpha, lambda value: value["allocationBoundary"].__setitem__("promoterRewardLeg", "PRESENT")),
                "expectedRejectCode": "REWARD_POLICY_SCHEMA_REJECT",
            },
            {
                "id": "policy_change_invalidates_hash",
                "baseCaseId": product["id"],
                "artifact": "REWARD_POLICY",
                "input": changed_policy,
                "expectedRejectCode": "REWARD_POLICY_TOKEN_HASH_MISMATCH",
            },
            {
                "id": "policy_signature_invalid",
                "baseCaseId": product["id"],
                "artifact": "REWARD_POLICY",
                "input": invalid_policy_signature,
                "expectedRejectCode": "REWARD_POLICY_SIGNATURE_INVALID",
            },
            {
                "id": "policy_must_precede_epoch_issuance",
                "baseCaseId": product["id"],
                "artifact": "REWARD_POLICY",
                "input": late_policy,
                "campaignEpoch": late_policy_epoch,
                "expectedRejectCode": "REWARD_POLICY_TIME_ORDER",
            },
            {
                "id": "epoch_must_bind_exact_direct_policy",
                "baseCaseId": product["id"],
                "artifact": "COMPOSITION",
                "campaignEpoch": mismatched_epoch,
                "input": policy,
                "expectedRejectCode": "CAMPAIGN_EPOCH_REWARD_POLICY_REF_MISMATCH",
            },
        ],
        "equivocationCases": [
            {
                "id": "same_reward_authority_and_policy_id_different_policy",
                "kind": "REWARD_POLICY",
                "baseCaseId": product["id"],
                "firstInput": policy,
                "secondInput": alternate_policy,
                "expectedRejectCode": "REWARD_POLICY_EQUIVOCATION",
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / VECTOR_PATH
    rendered = json.dumps(build_vectors(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not output_path.exists() or output_path.read_text(encoding="utf-8") != rendered:
            raise SystemExit(
                "Campaign direct-buyer-reward vector drift; run generator without --check"
            )
        print("[campaign-direct-buyer-reward-vectors] OK")
        return 0

    output_path.write_text(rendered, encoding="utf-8")
    print(f"[campaign-direct-buyer-reward-vectors] wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
