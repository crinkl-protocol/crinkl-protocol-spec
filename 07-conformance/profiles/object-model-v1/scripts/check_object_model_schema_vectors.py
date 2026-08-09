#!/usr/bin/env python3
"""OM4 object-model conformance checks.

Two checks, both driven by this one script (wired to two manifest kinds so
each contributes its own executed-kind entry in scripts/verify_conformance.mjs):

1. Draft 2020-12 schema-validation fixtures for the four OM4 schemas
   (VerificationPolicy, IssuerRegistrySnapshot, AttestationStatus,
   SpendPredicate): one valid instance MUST validate, one invalid instance
   MUST be rejected, per schema. Uses the same jsonschema.Draft202012Validator
   mechanism as
   07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/conformance/w3c-vc-2.0/v1/validate_draft202012.py.
2. Collapsed-artifact-kind rejection: `eligibilityProof` and `conversionProof`
   are not members of the thirteen-artifact canonical kind registry
   (README.md#core-objects) and MUST be rejected; ProofOfMatch and
   SpendPredicate (the objects that replaced the collapsed pair) MUST be
   accepted as positive controls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
if not (REPO / "README.md").is_file() or not (REPO / "07-conformance").is_dir():
    raise SystemExit(f"resolved REPO does not look like crinkl-protocol-spec: {REPO}")

SCHEMA_VECTOR = HERE.parents[0] / "conformance" / "v1" / "vectors" / "schema.objectModel.om4.v1.json"
KIND_VECTOR = REPO / "07-conformance" / "vectors" / "v1" / "vectors" / "objectModel.collapsedArtifactKind.rejected.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator_for(schema_relpath: str) -> Draft202012Validator:
    schema_path = REPO / schema_relpath
    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def check_schema_fixtures() -> tuple[int, int]:
    vector = read_json(SCHEMA_VECTOR)
    if vector.get("kind") != "schema.objectModel.om4.v1":
        raise ValueError(f"unexpected vector kind: {vector.get('kind')}")

    accepted = 0
    rejected = 0
    validators: dict[str, Draft202012Validator] = {}

    for case in vector["cases"]:
        schema_relpath = case["schemaPath"]
        if schema_relpath not in validators:
            validators[schema_relpath] = validator_for(schema_relpath)
        errors = list(validators[schema_relpath].iter_errors(case["instance"]))

        if case["expect"] == "accept":
            if errors:
                messages = "; ".join(e.message for e in errors)
                raise ValueError(f"{case['id']}: expected accept, got errors: {messages}")
            accepted += 1
        elif case["expect"] == "reject":
            if not errors:
                raise ValueError(f"{case['id']}: expected reject, but instance validated cleanly")
            rejected += 1
        else:
            raise ValueError(f"{case['id']}: unknown expect value {case['expect']!r}")

    return accepted, rejected


def check_collapsed_artifact_kinds() -> tuple[int, int]:
    vector = read_json(KIND_VECTOR)
    if vector.get("kind") != "objectModel.collapsedArtifactKind.rejected":
        raise ValueError(f"unexpected vector kind: {vector.get('kind')}")

    canonical = set(vector["canonicalKinds"])
    if len(canonical) != 13:
        raise ValueError(f"expected exactly thirteen canonical kinds, found {len(canonical)}")

    accepted = 0
    for case in vector["acceptCases"]:
        if case["kind"] not in canonical:
            raise ValueError(f"{case['id']}: {case['kind']} unexpectedly absent from canonical kinds")
        accepted += 1

    rejected = 0
    for case in vector["rejectCases"]:
        if case["kind"] in canonical:
            raise ValueError(f"{case['id']}: {case['kind']} unexpectedly present in canonical kinds")
        rejected += 1

    return accepted, rejected


def main() -> int:
    schema_accepted, schema_rejected = check_schema_fixtures()
    kind_accepted, kind_rejected = check_collapsed_artifact_kinds()
    print(
        "object-model OM4 schema fixtures: "
        f"{schema_accepted} accepted, {schema_rejected} rejected"
    )
    print(
        "object-model OM4 collapsed-artifact-kind registry: "
        f"{kind_accepted} canonical kinds accepted, {kind_rejected} collapsed kinds rejected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
