#!/usr/bin/env python3
"""Draft 2020-12 fixture validation for the W3C Spend Attestation profile."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CREDENTIAL_SCHEMA = REPO / "protocol/schemas/spend_attestation_credential_v1.schema.json"
HISTORY_SCHEMA = REPO / "protocol/schemas/w3c_issuer_key_history_v1.schema.json"
STATUS_CREDENTIAL_SCHEMA = REPO / "protocol/schemas/w3c_bitstring_status_list_credential_v1.schema.json"
VECTOR = HERE / "vectors/spend-attestation-credential.v1.json"
STATUS_VECTOR = HERE / "vectors/bitstring-status-list-credential.v1.json"
CURRENT_HISTORY = HERE / "fixtures/issuer-key-history-current.v1.json"
BOOTSTRAP_HISTORY = HERE / "fixtures/issuer-key-history-bootstrap.v1.json"
STATUS_HISTORY = HERE / "fixtures/issuer-key-history-status-current.v1.json"
FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date-time")
def is_profile_datetime(value):
    if not isinstance(value, str):
        return True
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return False
    return True


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def apply_mutation(value, mutation):
    target = value
    parts = [part.replace("~1", "/").replace("~0", "~") for part in mutation["path"][1:].split("/")]
    key = parts.pop()
    for part in parts:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if mutation["op"] == "remove":
        if isinstance(target, list):
            del target[int(key)]
        else:
            del target[key]
    elif mutation["op"] in {"add", "replace"}:
        if isinstance(target, list):
            target[int(key)] = mutation["value"]
        else:
            target[key] = mutation["value"]
    else:
        raise ValueError(f"unsupported mutation {mutation['op']}")


def validator_for(target: str):
    schema_path = {
        "credential": CREDENTIAL_SCHEMA,
        "history": HISTORY_SCHEMA,
        "keyHistory": HISTORY_SCHEMA,
        "statusCredential": STATUS_CREDENTIAL_SCHEMA,
    }[target]
    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FORMAT_CHECKER)


def errors_for(target: str, instance):
    return list(validator_for(target).iter_errors(instance))


def check():
    vector = read_json(VECTOR)
    status_vector = read_json(STATUS_VECTOR)
    credential = vector["valid"]["credential"]
    histories = [read_json(BOOTSTRAP_HISTORY), read_json(CURRENT_HISTORY), read_json(STATUS_HISTORY)]
    status_credentials = [
        read_json(HERE / "fixtures" / entry[fixture])
        for entry in status_vector["lists"]
        for fixture in ("clearFixture", "setFixture")
    ]
    if errors_for("credential", credential):
        raise ValueError("valid credential failed Draft 2020-12 validation")
    for history in histories:
        if errors_for("history", history):
            raise ValueError("valid issuer history failed Draft 2020-12 validation")
    for status_credential in status_credentials:
        if errors_for("statusCredential", status_credential):
            raise ValueError("valid status credential failed Draft 2020-12 validation")
    for case in vector["schemaRejectCases"]:
        source = credential if case["target"] == "credential" else histories[-1]
        candidate = json.loads(json.dumps(source))
        apply_mutation(candidate, case["mutation"])
        if not errors_for(case["target"], candidate):
            raise ValueError(f"{case['id']} unexpectedly passed Draft 2020-12 validation")
    for case in status_vector["schemaRejectCases"]:
        candidate = json.loads(json.dumps(status_credentials[0]))
        apply_mutation(candidate, case["mutation"])
        if not errors_for("statusCredential", candidate):
            raise ValueError(f"{case['id']} unexpectedly passed Draft 2020-12 validation")
    accepted = 1 + len(histories) + len(status_credentials)
    rejected = len(vector["schemaRejectCases"]) + len(status_vector["schemaRejectCases"])
    print(f"w3c Draft 2020-12 schema fixtures: {accepted} accepted, {rejected} rejected")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--target", choices=("credential", "history", "keyHistory", "statusCredential"))
    args = parser.parse_args()
    if args.check:
        check()
        return 0
    if not args.target:
        parser.error("--check or --target is required")
    instance = json.load(sys.stdin)
    errors = errors_for(args.target, instance)
    if errors:
        print("; ".join(error.message for error in errors), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
