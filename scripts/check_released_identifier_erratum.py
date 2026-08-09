#!/usr/bin/env python3
"""Verify the additive public erratum for released schema identifier collisions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ERRATUM_REL = "versions/errata/released-schema-identifier-collisions-v1.json"
INVENTORY_REL = "versions/identifier-inventory.json"
MARKDOWN_REL = "versions/errata/released-schema-identifier-collisions-v1.md"
CHANGELOG_REL = "versions/CHANGELOG.md"
EXPECTED_RECEIPT = "sha256:d2441f0da9fef029fc8f59b099458c3e7ff22ffd181c3ee3f9fd75525113ccf9"
EXPECTED_SUCCESSOR_COMMIT = "52648bae72a8c3b83883392be1c4ae714e4359c3"
EXPECTED_MAP_PATH = "protocol/artifacts/released_identifier_successor_map_v1.json"
EXPECTED_MAP_SHA256 = "sha256:a3a3c5977e42563982f4f555245b20eefeab831ec4d3b831e9122e291ba88fe4"
EXPECTED_INVENTORY_COMMIT = "bffe3ec9c95996524ca733628c1a9ca45e08be5a"
EXPECTED_SUCCESSOR_RECEIPT = "sha256:743f61538793f3f5d406c8f144c22344f35330b8b009c70e69ebfca57fbe8ba0"
EXPECTED_EFFECT = "OLD_IDENTITY_BYTES_PRESERVED; ADDITIVE_SUCCESSOR; CONSUMER_MIGRATION_EXPLICIT"

class DuplicateKeyError(ValueError):
    pass

def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result

def load_json(raw: bytes, location: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"{location}: invalid JSON: {exc}") from exc

def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def read_document(root: Path, rel: str) -> tuple[bytes, dict[str, Any]]:
    path = root / rel
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    document = load_json(raw, rel)
    require(isinstance(document, dict), f"{rel}: document must be an object")
    return raw, document

def receipt_lines(records: list[dict[str, Any]]) -> bytes:
    rows: list[str] = []
    for record in records:
        identifier, public, adopted = record.get("identifier"), record.get("public"), record.get("adopted")
        require(isinstance(identifier, str) and isinstance(public, dict) and isinstance(adopted, dict), "inventory collision record shape drift")
        public_digest, adopted_digest = public.get("sha256"), adopted.get("sha256")
        require(isinstance(public_digest, str) and isinstance(adopted_digest, str), "inventory collision digest missing")
        rows.append(f"{identifier}\t{public_digest}\t{adopted_digest}\n")
    require(rows == sorted(rows), "collision receipt records are not UTF-8 sorted")
    return "".join(rows).encode("utf-8")

def successor_receipt_lines(mappings: list[dict[str, Any]]) -> bytes:
    rows: list[str] = []
    for mapping in mappings:
        successor = mapping.get("successor")
        require(isinstance(successor, dict), "successor receipt mapping shape drift")
        old, successor_id, path, successor_digest = mapping.get("identifier"), successor.get("identifier"), successor.get("path"), successor.get("sha256")
        require(all(isinstance(value, str) and value for value in (old, successor_id, path, successor_digest)), "successor receipt mapping field missing")
        rows.append(f"{old}\t{successor_id}\t{path}\t{successor_digest}\n")
    require(rows == sorted(rows), "successor receipt records are not UTF-8 sorted")
    return "".join(rows).encode("utf-8")

def mapping_index(mappings: Any) -> dict[str, dict[str, Any]]:
    require(isinstance(mappings, list) and len(mappings) == 22, "erratum must contain exactly 22 mappings")
    result: dict[str, dict[str, Any]] = {}
    keys: list[str] = []
    for mapping in mappings:
        require(isinstance(mapping, dict), "erratum mapping must be an object")
        identifier = mapping.get("identifier")
        require(isinstance(identifier, str) and identifier, "erratum mapping identifier missing")
        require(identifier not in result, f"duplicate erratum mapping identifier: {identifier}")
        require(mapping.get("compatibilityEffect") == EXPECTED_EFFECT, f"compatibility effect drift: {identifier}")
        result[identifier] = mapping
        keys.append(identifier)
    require(keys == sorted(keys), "erratum mappings must be sorted by old identifier")
    return result

def validate_local(root: Path, erratum: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory_raw, inventory = read_document(root, INVENTORY_REL)
    if erratum is None:
        _, erratum = read_document(root, ERRATUM_REL)
    require(erratum.get("kind") == "crinkl.protocol.releasedSchemaIdentifierCollisionErratumV1", "erratum kind drift")
    require(erratum.get("status") == "SOURCE_CANDIDATE_NOT_PUBLISHED_OR_RELEASED", "erratum must remain an unpublished source candidate")
    source = erratum.get("publicInventory")
    require(isinstance(source, dict) and source == {"repository": "crinkl-protocol-spec", "artifactCommit": EXPECTED_INVENTORY_COMMIT, "auditedPublicSourceBase": inventory.get("publicSourceBase"), "path": INVENTORY_REL, "sha256": digest(inventory_raw)}, "erratum public inventory pin drift")
    git(root, "cat-file", "-e", f"{EXPECTED_INVENTORY_COMMIT}^{{commit}}")
    pinned_inventory = git(root, "show", f"{EXPECTED_INVENTORY_COMMIT}:{INVENTORY_REL}")
    require(pinned_inventory == inventory_raw and digest(pinned_inventory) == source["sha256"], "D2 inventory artifact-commit byte pin drift")
    receipt = inventory.get("effectiveCollisionReceipt")
    require(isinstance(receipt, dict) and erratum.get("effectiveCollisionReceipt") == receipt, "effective collision receipt drift")
    require(receipt.get("algorithm") == "sha256" and receipt.get("digest") == EXPECTED_RECEIPT and receipt.get("lineCount") == 22 and receipt.get("state") == "OBSERVED_UNRESOLVED_RELEASED_IDENTITY_COLLISION", "D4 effective receipt pin drift")
    comparisons = receipt.get("comparisons")
    require(isinstance(comparisons, list) and len(comparisons) == 2, "released collision comparisons drift")
    expected_tags = [{"tag": item.get("publicTag"), "commit": item.get("publicCommit")} for item in comparisons]
    require(erratum.get("releasedTagPins") == expected_tags, "immutable released tag pins drift")
    records = inventory.get("collisionRecords")
    require(isinstance(records, list) and len(records) == 22, "D2 collision inventory count drift")
    require(digest(receipt_lines(records)) == EXPECTED_RECEIPT, "D4 tab/LF UTF-8 receipt reproduction drift")
    mappings = mapping_index(erratum.get("mappings"))
    successor_receipt = erratum.get("successorReceipt")
    require(successor_receipt == {"algorithm": "sha256", "digest": EXPECTED_SUCCESSOR_RECEIPT, "lineCount": 22, "serialization": "oldIdentifier<TAB>successorIdentifier<TAB>successorPath<TAB>successorSha256<LF>", "state": "ADOPTED_ON_PROTECTED_MAIN_NOT_PUBLIC_SPEC_OR_RELEASED_OR_RUNTIME_OR_DEPLOYED"}, "successor receipt metadata drift")
    require(digest(successor_receipt_lines(erratum["mappings"])) == EXPECTED_SUCCESSOR_RECEIPT, "successor receipt reproduction drift")
    inventory_ids = [record.get("identifier") for record in records]
    require(inventory_ids == sorted(inventory_ids) and len(set(inventory_ids)) == 22, "D2 inventory identifiers must be sorted and unique")
    require(set(mappings) == set(inventory_ids), "erratum/D2 collision identifier set drift")
    binding_ids = [identifier for identifier in inventory_ids if isinstance(identifier, str) and identifier.startswith("crinkl://bindings/nats/crinkl-platform/v1/")]
    store_ids = [identifier for identifier in inventory_ids if identifier == "crinkl://protocol/schemas/store_location_entry_v1"]
    require(len(binding_ids) == 21 and len(store_ids) == 1, "erratum category/count drift")
    for record in records:
        identifier = record["identifier"]
        mapping = mappings[identifier]
        require(mapping.get("oldPublic") == record.get("public"), f"old public pin drift: {identifier}")
        require(mapping.get("oldAdopted") == record.get("adopted"), f"old adopted pin drift: {identifier}")
    # Each pinned release tag must resolve to its exact commit and preserve every
    # public-byte digest. This resolves by tag+path, never identifier alone.
    for comparison in comparisons:
        public_tag, public_commit = comparison.get("publicTag"), comparison.get("publicCommit")
        require(isinstance(public_tag, str) and isinstance(public_commit, str), "released tag pin shape drift")
        resolved = git(root, "rev-parse", f"refs/tags/{public_tag}^{{commit}}").decode("utf-8").strip()
        require(resolved == public_commit, f"released tag resolution drift: {public_tag}")
        for record in records:
            public = record["public"]
            raw_public = git(root, "show", f"{public_commit}:{public['path']}")
            require(digest(raw_public) == public["sha256"], f"released public-byte digest drift: {record['identifier']}@{public_tag}")
    successor_source = erratum.get("successorSourceMap")
    require(isinstance(successor_source, dict) and successor_source == {"repository": "crinkl-protocol", "commit": EXPECTED_SUCCESSOR_COMMIT, "path": EXPECTED_MAP_PATH, "sha256": EXPECTED_MAP_SHA256, "recordCount": 22, "state": "ADOPTED_ON_PROTECTED_MAIN_NOT_PUBLIC_SPEC_OR_RELEASED_OR_RUNTIME_OR_DEPLOYED"}, "D3.1 successor-source map pin drift")
    standing = erratum.get("standing")
    require(standing == {"releasedHistory": "IMMUTABLE", "identifierResolution": "ID_ONLY_RESOLUTION_UNSAFE_WHEN_BYTES_CONFLICT", "successorState": "ADOPTED_ON_PROTECTED_MAIN_NOT_PUBLIC_SPEC_OR_RELEASED_OR_RUNTIME_OR_DEPLOYED", "consumerMigration": "EXPLICIT_AND_INACTIVE"}, "erratum standing/compatibility drift")
    return erratum

def git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        raise ValueError(f"cannot run git in {root}: {exc}") from exc
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} in {root} failed: {detail or f'exit {result.returncode}'}")
    return result.stdout

def validate_full(root: Path, adopted_root: Path, erratum: dict[str, Any] | None = None) -> None:
    erratum = validate_local(root, erratum)
    require(adopted_root.is_dir(), f"adopted repository does not exist: {adopted_root}")
    git(adopted_root, "cat-file", "-e", f"{EXPECTED_SUCCESSOR_COMMIT}^{{commit}}")
    raw_map = git(adopted_root, "show", f"{EXPECTED_SUCCESSOR_COMMIT}:{EXPECTED_MAP_PATH}")
    require(digest(raw_map) == EXPECTED_MAP_SHA256, "D3.1 raw successor-map digest drift")
    successor_map = load_json(raw_map, f"{EXPECTED_SUCCESSOR_COMMIT}:{EXPECTED_MAP_PATH}")
    require(isinstance(successor_map, dict) and successor_map.get("kind") == "crinkl.protocol.releasedIdentifierSuccessorMapV1" and successor_map.get("mapVersion") == 1, "D3.1 successor-map identity drift")
    require(successor_map.get("canonicalCollisionReceipt") == EXPECTED_RECEIPT, "D3.1/D4 receipt link drift")
    map_records = successor_map.get("records")
    require(isinstance(map_records, list) and len(map_records) == 22, "D3.1 successor-map record count drift")
    map_by_old: dict[str, dict[str, Any]] = {}
    for record in map_records:
        require(isinstance(record, dict) and isinstance(record.get("oldIdentifier"), str), "D3.1 map record shape drift")
        old = record["oldIdentifier"]
        require(old not in map_by_old, f"duplicate D3.1 map old identifier: {old}")
        map_by_old[old] = record
    mappings = mapping_index(erratum["mappings"])
    require(set(map_by_old) == set(mappings), "erratum/D3.1 mapping set drift")
    for old, mapping in mappings.items():
        record = map_by_old[old]
        require(mapping.get("oldPublic") == record.get("oldPublic") and mapping.get("oldAdopted") == record.get("oldAdopted"), f"D3.1 old-byte pin drift: {old}")
        require(mapping.get("successor") == record.get("newSuccessor"), f"D3.1 successor pin drift: {old}")
        require(record.get("compatibilityEffect") == EXPECTED_EFFECT, f"D3.1 compatibility effect drift: {old}")
        successor = mapping["successor"]
        require(isinstance(successor, dict) and isinstance(successor.get("identifier"), str) and isinstance(successor.get("path"), str), f"successor shape drift: {old}")
        raw_schema = git(adopted_root, "show", f"{EXPECTED_SUCCESSOR_COMMIT}:{successor['path']}")
        require(digest(raw_schema) == successor.get("sha256"), f"successor schema digest drift: {old}")
        schema = load_json(raw_schema, f"{EXPECTED_SUCCESSOR_COMMIT}:{successor['path']}")
        require(isinstance(schema, dict) and schema.get("$id") == successor["identifier"], f"successor schema $id drift: {old}")

def validate_docs(root: Path) -> None:
    try:
        markdown = (root / MARKDOWN_REL).read_text(encoding="utf-8")
        changelog = (root / CHANGELOG_REL).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"erratum documentation missing: {exc}") from exc
    require("# Released schema identifier collision erratum (v1)" in markdown, "erratum markdown heading missing")
    require("[machine-readable erratum](released-schema-identifier-collisions-v1.json)" in markdown, "erratum markdown JSON link missing")
    require("22 mappings: 21 NATS binding schemas and one store schema." in markdown, "erratum markdown category/count statement missing")
    require(EXPECTED_SUCCESSOR_COMMIT in markdown and "release/tag+digest" in markdown and "already unsafe" in markdown and "released tags/full Git objects" in markdown, "erratum markdown resolution/source wording missing")
    require("[released schema identifier collision erratum](errata/released-schema-identifier-collisions-v1.md)" in changelog, "changelog erratum link missing")
    require("## Schema identifier erratum candidate (not published)" in changelog, "changelog erratum candidate heading missing")

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-only", action="store_true", help="validate only checked-in public evidence")
    parser.add_argument("--adopted-repo", type=Path, help="path to an adopted crinkl-protocol checkout")
    parsed = parser.parse_args(argv)
    if not parsed.local_only and parsed.adopted_repo is None:
        fallback = os.environ.get("CRINKL_PROTOCOL_ADOPTED_REPO")
        if fallback:
            parsed.adopted_repo = Path(fallback)
        else:
            parser.error("--adopted-repo or CRINKL_PROTOCOL_ADOPTED_REPO is required unless --local-only is used")
    return parsed

def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        erratum = validate_local(ROOT)
        validate_docs(ROOT)
        if args.local_only:
            print("[released-identifier-erratum] OK (local-only; 22 mappings, D4 receipt reproduced)")
        else:
            validate_full(ROOT, args.adopted_repo.resolve(), erratum)
            print("[released-identifier-erratum] OK (full; exact D3.1 Git objects, 22 successor schemas)")
        return 0
    except ValueError as exc:
        print(f"[released-identifier-erratum] {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
