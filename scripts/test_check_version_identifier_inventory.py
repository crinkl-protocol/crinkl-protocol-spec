#!/usr/bin/env python3
"""Focused hostile tests for the version-identifier inventory gate."""
from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path

import check_version_identifier_inventory as checker


ROOT = Path(__file__).resolve().parents[1]


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adopted-repo", type=Path, default=os.environ.get("CRINKL_PROTOCOL_ADOPTED_REPO"))
    parsed = parser.parse_args()
    if parsed.adopted_repo is None:
        parser.error("--adopted-repo or CRINKL_PROTOCOL_ADOPTED_REPO is required")
    return parsed


def rejected(name: str, inventory: dict, adopted_root: Path) -> None:
    try:
        checker.validate_inventory(ROOT, adopted_root, inventory)
    except ValueError:
        print(f"[identifier-inventory-test] rejected: {name}")
        return
    raise AssertionError(f"{name}: mutation was accepted")


def main() -> int:
    parsed = args()
    adopted_root = parsed.adopted_repo.resolve()
    inventory = checker.load_inventory()
    checker.validate_inventory(ROOT, adopted_root, inventory)
    print("[identifier-inventory-test] accepted: current inventory")

    mutated = copy.deepcopy(inventory)
    mutated["requiredAliases"][0]["title"] = "WrongTitleV1"
    rejected("missing required alias", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["requiredAliases"][0]["surface"] = "wireProtocol"
    rejected("cross-surface alias", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["repositories"]["public"]["rules"].append({"prefix": "bindings/", "surface": "wireProtocol"})
    rejected("discovery rule overlap", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["repositories"]["public"]["exclusions"].append("hidden/")
    rejected("arbitrary discovery exclusion", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["repositories"]["public"]["rules"] = [rule for rule in mutated["repositories"]["public"]["rules"] if rule["prefix"] != "bindings/"]
    rejected("unclassified structured path", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["effectiveCollisionReceipt"]["digest"] = "sha256:" + "0" * 64
    rejected("wrong effective receipt", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["effectiveCollisionReceipt"]["comparisons"] = []
    rejected("empty receipt comparisons", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["effectiveCollisionReceipt"]["comparisons"] = mutated["effectiveCollisionReceipt"]["comparisons"][:1]
    rejected("one receipt comparison", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["effectiveCollisionReceipt"]["state"] = "MUTATED"
    rejected("wrong receipt state", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["effectiveCollisionReceipt"]["algorithm"] = "sha512"
    rejected("D4 registry receipt mismatch", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["collisionRecords"].pop()
    rejected("missing known collision record", mutated, adopted_root)

    mutated = copy.deepcopy(inventory)
    mutated["adoptedMainAtAudit"] = "0" * 40
    rejected("wrong adopted audit pin", mutated, adopted_root)

    try:
        checker.field_role("unknownVersion", "objectSchema")
    except ValueError:
        print("[identifier-inventory-test] rejected: unclassified version field")
    else:
        raise AssertionError("unknown version field was accepted")

    public = {"crinkl://example/id": ("public.json", "objectSchema", "sha256:" + "a" * 64)}
    adopted = {"crinkl://example/id": ("adopted.json", "objectSchema", "sha256:" + "b" * 64)}
    try:
        checker.validate_current_identifier_collisions(public, adopted, {})
    except ValueError:
        print("[identifier-inventory-test] rejected: unknown current identifier collision")
    else:
        raise AssertionError("unknown current identifier collision was accepted")

    recorded = {"crinkl://example/id": ("public.json", "sha256:" + "a" * 64, "adopted.json", "sha256:" + "b" * 64)}
    try:
        checker.validate_current_identifier_collisions({}, {}, recorded)
    except ValueError:
        print("[identifier-inventory-test] rejected: recorded collision absence")
    else:
        raise AssertionError("recorded collision absence was accepted")

    equal_current_public = {"crinkl://example/id": ("public.json", "objectSchema", "sha256:" + "c" * 64)}
    equal_current_adopted = {"crinkl://example/id": ("adopted.json", "objectSchema", "sha256:" + "c" * 64)}
    try:
        checker.validate_current_identifier_collisions(equal_current_public, equal_current_adopted, recorded)
    except ValueError:
        print("[identifier-inventory-test] rejected: recorded collision current-byte mutation")
    else:
        raise AssertionError("recorded collision current-byte mutation was accepted")

    try:
        checker.validate_artifact_aliases("schemas/example_v1.schema.json", "objectSchema", {"$id": "crinkl://example_v2", "title": "ExampleV1"})
    except ValueError:
        print("[identifier-inventory-test] rejected: object-schema alias mismatch")
    else:
        raise AssertionError("object-schema alias mismatch was accepted")

    try:
        checker.validate_artifact_aliases("schemas/example_v1.schema.json", "objectSchema", {"$id": "crinkl://example", "title": "ExampleV1"})
    except ValueError:
        print("[identifier-inventory-test] rejected: object-schema missing identifier version")
    else:
        raise AssertionError("object-schema missing identifier version was accepted")

    try:
        checker.validate_artifact_aliases("schemas/example_v1.schema.json", "objectSchema", {"title": "ExampleV1"})
    except ValueError:
        print("[identifier-inventory-test] rejected: object-schema missing root identifier")
    else:
        raise AssertionError("object-schema missing root identifier was accepted")

    try:
        checker.version_field_role("unknownVersions", "objectSchema")
    except ValueError:
        print("[identifier-inventory-test] rejected: unclassified JSON versions field")
    else:
        raise AssertionError("unknown JSON versions field was accepted")

    try:
        checker.validate_artifact_aliases("bindings/nats/example/v1/schemas/event.schema.json", "bindingContextCryptographicDomain", {"$id": "crinkl://bindings/nats/example/v2/event"})
    except ValueError:
        print("[identifier-inventory-test] rejected: binding namespace alias mismatch")
    else:
        raise AssertionError("binding namespace alias mismatch was accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
