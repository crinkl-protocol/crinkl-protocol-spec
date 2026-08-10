#!/usr/bin/env python3
"""Executable object-model candidate conformance checks.

The checker owns the thirteen-kind protocol-object registry. Vectors provide
whole artifact envelopes as inputs; they do not define which kinds are valid.
The four candidate schemas are checked structurally and then by the semantic
rules JSON Schema cannot express, including content-address recomputation and
timestamp ordering.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
if not (REPO / "README.md").is_file() or not (REPO / "07-conformance").is_dir():
    raise SystemExit(f"resolved REPO does not look like crinkl-protocol-spec: {REPO}")

SCHEMA_VECTOR = (
    HERE.parents[0]
    / "conformance"
    / "v1"
    / "vectors"
    / "schema.objectModel.om4.v1.json"
)
KIND_VECTOR = (
    REPO
    / "07-conformance"
    / "vectors"
    / "v1"
    / "vectors"
    / "objectModel.collapsedArtifactKind.rejected.json"
)

CANONICAL_KINDS = frozenset(
    {
        "SpendStreamEvent",
        "SpendAttestation",
        "VerificationPolicy",
        "IssuerRegistrySnapshot",
        "AttestationStatus",
        "SpendAttestationToken",
        "SpendAttestationCredential",
        "SpendPredicate",
        "ProofOfMatch",
        "CampaignEpoch",
        "FinalityCertificate",
        "RewardCommitment",
        "CampaignSettlementCommitment",
    }
)

SCHEMA_PATH_TO_KIND = {
    "protocol/core/schemas/verification_policy_v1.schema.json": "VerificationPolicy",
    "protocol/core/schemas/issuer_registry_snapshot_v1.schema.json": "IssuerRegistrySnapshot",
    "protocol/core/schemas/attestation_status_v1.schema.json": "AttestationStatus",
    "protocol/applications/conditions/schemas/spend_predicate_v1.schema.json": "SpendPredicate",
}
KIND_TO_SCHEMA_PATH = {kind: path for path, kind in SCHEMA_PATH_TO_KIND.items()}


class SemanticValidationError(ValueError):
    """An instance is structurally valid but violates an executable contract."""


JCS_NODE_PROGRAM = r"""
const chunks = [];
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => chunks.push(chunk));
process.stdin.on("end", () => {
  const hasLoneSurrogate = (value) => {
    for (let index = 0; index < value.length; index += 1) {
      const unit = value.charCodeAt(index);
      if (unit >= 0xd800 && unit <= 0xdbff) {
        const next = value.charCodeAt(index + 1);
        if (!(next >= 0xdc00 && next <= 0xdfff)) return true;
        index += 1;
      } else if (unit >= 0xdc00 && unit <= 0xdfff) {
        return true;
      }
    }
    return false;
  };
  const canonicalize = (value) => {
    if (value === null) return "null";
    if (typeof value === "boolean") return value ? "true" : "false";
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new TypeError("non-finite JCS number");
      return JSON.stringify(value);
    }
    if (typeof value === "string") {
      if (hasLoneSurrogate(value)) throw new TypeError("lone surrogate in JCS string");
      return JSON.stringify(value);
    }
    if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
    if (typeof value === "object") {
      return `{${Object.keys(value).sort().map((key) =>
        `${canonicalize(key)}:${canonicalize(value[key])}`).join(",")}}`;
    }
    throw new TypeError(`unsupported JCS value: ${typeof value}`);
  };
  process.stdout.write(canonicalize(JSON.parse(chunks.join(""))));
});
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonicalize(value: Any) -> str:
    """Return RFC 8785/JCS bytes using ECMAScript number and key semantics."""

    serialized = json.dumps(
        value, allow_nan=False, ensure_ascii=True, separators=(",", ":")
    )
    result = subprocess.run(
        ["node", "-e", JCS_NODE_PROGRAM],
        input=serialized,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"node exited {result.returncode}"
        raise SemanticValidationError(f"JCS canonicalization failed: {detail}")
    return result.stdout


def content_address(value: Any) -> str:
    digest = hashlib.sha256(canonicalize(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as exc:
        raise SemanticValidationError(f"{label} is not a valid millisecond UTC timestamp") from exc
    return parsed.replace(tzinfo=timezone.utc)


def validator_for(schema_relpath: str) -> Draft202012Validator:
    schema = read_json(REPO / schema_relpath)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


VALIDATORS = {
    kind: validator_for(schema_path) for kind, schema_path in KIND_TO_SCHEMA_PATH.items()
}


def check_semantics(kind: str, instance: dict[str, Any]) -> None:
    if kind == "VerificationPolicy":
        expected = content_address(instance["rules"])
        if instance["policyId"] != expected:
            raise SemanticValidationError(
                f"policyId mismatch: declared {instance['policyId']}, computed {expected}"
            )
        if "effectiveFrom" in instance:
            parse_timestamp(instance["effectiveFrom"], "effectiveFrom")
        return

    if kind == "SpendPredicate":
        hash_input = {key: value for key, value in instance.items() if key != "predicateHash"}
        expected = content_address(hash_input)
        if instance["predicateHash"] != expected:
            raise SemanticValidationError(
                f"predicateHash mismatch: declared {instance['predicateHash']}, computed {expected}"
            )
        return

    if kind == "IssuerRegistrySnapshot":
        parse_timestamp(instance["asOf"], "asOf")
        for index, key in enumerate(instance["keys"]):
            valid_from = parse_timestamp(key["validFrom"], f"keys[{index}].validFrom")
            if key["validUntil"] is not None:
                valid_until = parse_timestamp(
                    key["validUntil"], f"keys[{index}].validUntil"
                )
                if valid_until <= valid_from:
                    raise SemanticValidationError(
                        f"keys[{index}].validUntil must be later than validFrom"
                    )
        return

    if kind == "AttestationStatus":
        parse_timestamp(instance["asOf"], "asOf")
        return


def validate_candidate_payload(kind: str, instance: Any) -> None:
    if kind not in VALIDATORS:
        raise ValueError(f"no candidate schema registered for {kind}")
    if not isinstance(instance, dict):
        raise ValueError(f"{kind} payload must be an object")
    errors = sorted(
        VALIDATORS[kind].iter_errors(instance),
        key=lambda item: tuple(str(part) for part in item.path),
    )
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise ValueError(f"schema validation failed: {messages}")
    check_semantics(kind, instance)


def validate_protocol_object(artifact: Any) -> None:
    """Dispatch one whole protocol-object envelope through the shipped registry."""

    if not isinstance(artifact, dict):
        raise ValueError("artifact envelope must be an object")
    if set(artifact) != {"kind", "payload"}:
        raise ValueError("artifact envelope must contain exactly kind and payload")
    kind = artifact["kind"]
    payload = artifact["payload"]
    if not isinstance(kind, str) or kind not in CANONICAL_KINDS:
        raise ValueError(f"unsupported protocol object kind: {kind!r}")
    if not isinstance(payload, dict):
        raise ValueError(f"{kind} payload must be an object")
    if kind in VALIDATORS:
        validate_candidate_payload(kind, payload)


def check_schema_fixtures() -> tuple[int, int]:
    vector = read_json(SCHEMA_VECTOR)
    if vector.get("kind") != "schema.objectModel.om4.v1":
        raise ValueError(f"unexpected vector kind: {vector.get('kind')}")

    accepted = 0
    rejected = 0
    for case in vector["cases"]:
        schema_path = case["schemaPath"]
        kind = SCHEMA_PATH_TO_KIND.get(schema_path)
        if kind is None:
            raise ValueError(f"{case['id']}: unregistered schema path {schema_path}")

        schema_errors = sorted(
            VALIDATORS[kind].iter_errors(case["instance"]),
            key=lambda item: tuple(str(part) for part in item.path),
        )
        semantic_error: SemanticValidationError | None = None
        if not schema_errors:
            try:
                check_semantics(kind, case["instance"])
            except SemanticValidationError as exc:
                semantic_error = exc

        if case["expect"] == "accept":
            if schema_errors or semantic_error is not None:
                messages = "; ".join(error.message for error in schema_errors)
                detail = messages or str(semantic_error)
                raise ValueError(f"{case['id']}: expected accept, got {detail}")
            accepted += 1
            continue

        if case["expect"] != "reject":
            raise ValueError(f"{case['id']}: unknown expect value {case['expect']!r}")

        expected_stage = case.get("expectStage")
        if expected_stage == "schema" and not schema_errors:
            raise ValueError(f"{case['id']}: expected schema rejection")
        if expected_stage == "semantic":
            if schema_errors:
                messages = "; ".join(error.message for error in schema_errors)
                raise ValueError(
                    f"{case['id']}: expected semantic rejection, got schema errors: {messages}"
                )
            if semantic_error is None:
                raise ValueError(f"{case['id']}: expected semantic rejection")
        if expected_stage not in {"schema", "semantic"}:
            raise ValueError(f"{case['id']}: invalid expectStage {expected_stage!r}")
        rejected += 1

    return accepted, rejected


def check_collapsed_artifact_kinds() -> tuple[int, int]:
    vector = read_json(KIND_VECTOR)
    if vector.get("kind") != "objectModel.collapsedArtifactKind.rejected":
        raise ValueError(f"unexpected vector kind: {vector.get('kind')}")
    if len(CANONICAL_KINDS) != 13:
        raise ValueError(f"shipped registry must contain thirteen kinds, found {len(CANONICAL_KINDS)}")

    accepted = 0
    rejected = 0
    for case in vector["cases"]:
        try:
            validate_protocol_object(case["artifact"])
            error: ValueError | None = None
        except ValueError as exc:
            error = exc

        if case["expect"] == "accept":
            if error is not None:
                raise ValueError(f"{case['id']}: expected accept, got {error}")
            accepted += 1
        elif case["expect"] == "reject":
            if error is None:
                raise ValueError(f"{case['id']}: expected rejection")
            rejected += 1
        else:
            raise ValueError(f"{case['id']}: unknown expect value {case['expect']!r}")

    return accepted, rejected


def main() -> int:
    schema_accepted, schema_rejected = check_schema_fixtures()
    kind_accepted, kind_rejected = check_collapsed_artifact_kinds()
    print(
        "object-model OM4r schema fixtures: "
        f"{schema_accepted} accepted, {schema_rejected} rejected"
    )
    print(
        "object-model protocol-object dispatcher: "
        f"{kind_accepted} canonical artifacts accepted, "
        f"{kind_rejected} collapsed artifacts rejected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
