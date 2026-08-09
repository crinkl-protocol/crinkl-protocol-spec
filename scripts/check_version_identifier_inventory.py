#!/usr/bin/env python3
"""Check the authoritative structured version-identifier inventory.

The public checkout is read as a working source tree.  The adopted checkout is
read only through named Git objects, so its checked-out branch and worktree
state have no authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "versions" / "identifier-inventory.json"
RELEASE_REGISTRY_PATH = ROOT / "versions" / "release-registry.json"
STRUCTURED_SUFFIXES = (".json", ".yaml", ".yml")
VERSION_PATH = re.compile(r"(?:^|[._/-])v\d+(?:[._/-]|$)", re.IGNORECASE)
YAML_KEY = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:")
FILENAME_VERSION = re.compile(r"(?:[_\.-]v)(\d+)(?:\.schema)?\.json$", re.IGNORECASE)
IDENTIFIER_VERSION = re.compile(r"(?:[_\./-]v)(\d+)(?:\.schema\.json)?$", re.IGNORECASE)
TITLE_VERSION = re.compile(r"V(\d+)$")
VERSION_FIELDS = {
    "acceptedContextSchemaVersions", "artifactVersion", "artifactVersions", "bindingVersion", "bundleVersion", "conformanceSuiteVersion", "contractVersion", "decisionVersion", "inventoryVersion",
    "defaultBindingProtocolVersion", "epochVersion", "expectedDayProjectionVersion",
    "expectedFrontierProjectionVersion", "latestReleasedVersion", "ledgerVersion",
    "manifestSchemaVersion", "manifestVersion", "originalVerificationVersion",
    "pdaDerivationVersion", "planVersion", "policyVersion", "predicateVersion",
    "producerVersion", "profileVersion", "projectionVersion", "protocolObjectVersion",
    "protocolVersion", "publicReleaseVersionIsNotWireProtocolVersion",
    "publicRepositoryVersion", "registryVersion", "releaseVersion", "repositoryVersion",
    "requiredConformanceSuiteVersion", "requiredSchemaVersions", "reviewedCandidateVersion", "rootFormulaVersion",
    "retainedVersions", "schemaVersion", "storageAdapterVersion", "suiteVersion", "supportedSchemaVersions", "supportedWireProtocolVersions", "unsupported-required-version",
    "validFromProtocolVersion", "vectorVersion", "verificationVersion", "version",
    "acceptedProtocolVersions",
}
IDENTIFIER_ROLES = {
    "$id": "rootId", "title": "title", "type": "type", "kind": "manifestKind",
    "context": "context", "domain": "cryptographicDomain",
}


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_json_bytes(raw: bytes, location: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"{location}: invalid JSON: {exc}") from exc


def load_inventory(path: Path = INVENTORY_PATH) -> dict[str, Any]:
    document = load_json_bytes(path.read_bytes(), str(path))
    if not isinstance(document, dict) or document.get("inventoryVersion") != 1:
        raise ValueError("identifier inventory identity drift")
    return document


def git(root: Path, *args: str, binary: bool = False) -> bytes | str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
    except OSError as exc:
        raise ValueError(f"cannot run git in {root}: {exc}") from exc
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} in {root} failed: {detail or f'exit {result.returncode}'}")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def public_paths(root: Path) -> list[str]:
    names = git(root, "ls-files", "-z", binary=True)
    assert isinstance(names, bytes)
    return sorted(part.decode("utf-8") for part in names.split(b"\0") if part)


def adopted_paths(root: Path, commit: str) -> list[str]:
    git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    names = git(root, "ls-tree", "-r", "-z", "--name-only", commit, binary=True)
    assert isinstance(names, bytes)
    return sorted(part.decode("utf-8") for part in names.split(b"\0") if part)


def bytes_for(repository: str, root: Path, commit: str | None, path: str) -> bytes:
    if repository == "public":
        return (root / path).read_bytes()
    raw = git(root, "show", f"{commit}:{path}", binary=True)
    assert isinstance(raw, bytes)
    return raw


def classify_path(path: str, rules: list[dict[str, Any]], exclusions: list[str]) -> str:
    matches = [rule["surface"] for rule in rules if path.startswith(str(rule.get("prefix") or ""))]
    excluded = [prefix for prefix in exclusions if path.startswith(prefix)]
    if excluded and matches:
        raise ValueError(f"discovery exclusion overlap: {path}")
    if excluded:
        return "excluded"
    if len(matches) != 1:
        raise ValueError(f"unclassified structured path: {path}")
    return str(matches[0])


def walk_json(node: Any, pointer: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(node, dict):
        for key in sorted(node):
            value = node[key]
            child = f"{pointer}.{key}"
            yield child, key, value
            yield from walk_json(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_json(value, f"{pointer}[{index}]")


def field_role(key: str, path_surface: str) -> tuple[str, str]:
    if key not in VERSION_FIELDS:
        raise ValueError(f"unclassified version field: {key}")
    if key == "policyVersion":
        return "objectSchema", "instanceRevision"
    if key in {"protocolVersion", "defaultBindingProtocolVersion", "validFromProtocolVersion", "protocolObjectVersion", "acceptedProtocolVersions", "supportedWireProtocolVersions"}:
        return "wireProtocol", "embeddedVersion"
    if key in {"acceptedContextSchemaVersions", "schemaVersion", "manifestSchemaVersion", "requiredSchemaVersions", "supportedSchemaVersions"}:
        return "objectSchema", "embeddedVersion"
    if key in {"profileVersion", "suiteVersion", "conformanceSuiteVersion", "requiredConformanceSuiteVersion", "vectorVersion"}:
        return "profileConformanceSuite", "embeddedVersion"
    if key in {"releaseVersion", "latestReleasedVersion", "reviewedCandidateVersion", "publicReleaseVersionIsNotWireProtocolVersion", "publicRepositoryVersion", "repositoryVersion"}:
        return "specificationRelease", "embeddedVersion"
    return path_surface, "embeddedVersion"


def version_field_role(key: str, path_surface: str) -> tuple[str, str] | None:
    if key in VERSION_FIELDS:
        return field_role(key, path_surface)
    if key.lower().endswith(("version", "versions")):
        raise ValueError(f"unclassified version field: {key}")
    return None


def version_part(pattern: re.Pattern[str], value: Any) -> str | None:
    match = pattern.search(value) if isinstance(value, str) else None
    return match.group(1) if match else None


def validate_artifact_aliases(path: str, surface: str, document: dict[str, Any]) -> None:
    """Validate independently named artifact aliases without borrowing directory versions."""
    if surface == "objectSchema":
        filename_version = version_part(FILENAME_VERSION, Path(path).name)
        identifier = document.get("$id")
        title = document.get("title")
        identifier_version = version_part(IDENTIFIER_VERSION, identifier)
        title_version = version_part(TITLE_VERSION, title)
        if filename_version is not None and (not isinstance(identifier, str) or not identifier or identifier_version is None):
            raise ValueError(f"object-schema identifier is missing filename version: {path}")
        if filename_version is not None and isinstance(title, str) and title_version is None:
            raise ValueError(f"object-schema title is missing filename version: {path}")
        values = [value for value in (filename_version, identifier_version, title_version) if value is not None]
        if len(set(values)) > 1:
            raise ValueError(f"object-schema aliases disagree: {path}")
    if surface == "bindingContextCryptographicDomain" and path.startswith("bindings/"):
        namespace = re.search(r"/v(\d+)/", path)
        identifier_namespace = re.search(r"/v(\d+)/", str(document.get("$id") or ""))
        if namespace and (not identifier_namespace or namespace.group(1) != identifier_namespace.group(1)):
            raise ValueError(f"binding namespace aliases disagree: {path}")


def path_subrole(path: str) -> str:
    """Keep concrete inventory kinds visible below their shared compatibility surface."""
    lowered = path.lower()
    if "/vectors/" in lowered or "/fixtures/" in lowered:
        return "vector"
    if Path(path).name == "manifest.json" or path.endswith(".schema-manifest.json"):
        return "manifest"
    if "/profiles/" in lowered or "profile" in Path(path).stem.lower():
        return "profile"
    if "/conformance/" in lowered or lowered.startswith("conformance/"):
        return "conformanceSuite"
    if "/context/" in lowered:
        return "context"
    if lowered.startswith("bindings/"):
        return "binding"
    if "domain" in Path(path).stem.lower():
        return "cryptographicDomain"
    return "artifact"


def schema_ids(repository: str, root: Path, commit: str | None, entries: list[tuple[str, str]]) -> dict[str, tuple[str, str, str]]:
    found: dict[str, tuple[str, str, str]] = {}
    for path, surface in entries:
        if not path.endswith(".json"):
            continue
        raw = bytes_for(repository, root, commit, path)
        document = load_json_bytes(raw, f"{repository}:{path}")
        if not isinstance(document, dict):
            continue
        validate_artifact_aliases(path, surface, document)
        identifier = document.get("$id")
        if not isinstance(identifier, str) or not identifier:
            continue
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        if identifier in found and found[identifier][2] != digest:
            raise ValueError(f"duplicate canonical identifier with different {repository} bytes: {identifier}")
        found[identifier] = (path, surface, digest)
    return found


def validate_aliases(inventory: dict[str, Any], public_root: Path) -> None:
    for alias in inventory.get("requiredAliases") or []:
        if alias.get("repository") != "public":
            raise ValueError("unsupported required alias repository")
        path = str(alias.get("path") or "")
        document = load_json_bytes((public_root / path).read_bytes(), path)
        if not isinstance(document, dict):
            raise ValueError(f"alias artifact is not an object: {path}")
        if Path(path).name != alias.get("filename") or document.get("$id") != alias.get("$id") or document.get("title") != alias.get("title"):
            raise ValueError(f"required aliases disagree: {path}")
        if alias.get("surface") != "objectSchema":
            raise ValueError(f"cross-surface aliasing: {path}")
        field = alias.get("instanceRevisionField")
        if field not in document.get("properties", {}):
            raise ValueError(f"missing required instance revision field: {path}:{field}")
        surface, role = field_role(str(field), "objectSchema")
        if (surface, role) != ("objectSchema", "instanceRevision"):
            raise ValueError(f"policyVersion alias role drift: {path}")


def collision_lines(public_root: Path, adopted_root: Path, comparison: dict[str, Any]) -> list[tuple[str, str, str, str, str]]:
    tag = str(comparison["publicTag"])
    public_commit = str(comparison["publicCommit"])
    adopted_commit = str(comparison["adoptedCommit"])
    if git(public_root, "rev-parse", f"refs/tags/{tag}^{{commit}}") != public_commit:
        raise ValueError(f"collision tag pin drift: {tag}")
    public = schema_ids_at_commit(public_root, public_commit)
    adopted = schema_ids_at_commit(adopted_root, adopted_commit)
    rows = []
    for identifier in sorted(set(public) & set(adopted)):
        public_path, public_digest = public[identifier]
        adopted_path, adopted_digest = adopted[identifier]
        if public_digest != adopted_digest:
            rows.append((identifier, public_path, public_digest, adopted_path, adopted_digest))
    return rows


def schema_ids_at_commit(root: Path, commit: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for path in adopted_paths(root, commit):
        if not path.endswith(".json"):
            continue
        raw = git(root, "show", f"{commit}:{path}", binary=True)
        assert isinstance(raw, bytes)
        document = load_json_bytes(raw, f"{commit}:{path}")
        if not isinstance(document, dict) or not isinstance(document.get("$id"), str):
            continue
        identifier = document["$id"]
        if identifier in result:
            raise ValueError(f"duplicate historical identifier: {identifier}")
        result[identifier] = (path, "sha256:" + hashlib.sha256(raw).hexdigest())
    return result


def effective_receipt_from_registry(public_root: Path) -> dict[str, Any]:
    registry = load_json_bytes((public_root / "versions" / "release-registry.json").read_bytes(), str(RELEASE_REGISTRY_PATH))
    corrections = registry.get("collisionReceiptCorrections") if isinstance(registry, dict) else None
    if not isinstance(corrections, list) or not corrections or not isinstance(corrections[-1], dict):
        raise ValueError("D4 registry has no effective collision receipt")
    receipt = corrections[-1].get("effectiveReceipt")
    if not isinstance(receipt, dict):
        raise ValueError("D4 registry effective collision receipt is invalid")
    return receipt


def validate_collision_receipt(inventory: dict[str, Any], public_root: Path, adopted_root: Path) -> dict[str, tuple[str, str, str, str]]:
    receipt = inventory.get("effectiveCollisionReceipt") or {}
    if receipt != effective_receipt_from_registry(public_root):
        raise ValueError("effective collision receipt does not equal D4 registry")
    records = inventory.get("collisionRecords") or []
    expected = [(item.get("identifier"), item.get("public", {}).get("path"), item.get("public", {}).get("sha256"), item.get("adopted", {}).get("path"), item.get("adopted", {}).get("sha256")) for item in records]
    if len(expected) != int(receipt.get("lineCount") or -1) or len(set(expected)) != len(expected):
        raise ValueError("collision record count or uniqueness drift")
    canonical = "".join(f"{identifier}\t{public_digest}\t{adopted_digest}\n" for identifier, _, public_digest, _, adopted_digest in sorted(expected))
    if "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest() != receipt.get("digest"):
        raise ValueError("effective collision receipt digest drift")
    for comparison in receipt.get("comparisons") or []:
        observed = collision_lines(public_root, adopted_root, comparison)
        if sorted(observed) != sorted(expected):
            raise ValueError("effective collision records do not reproduce pinned comparison")
    return {str(identifier): (str(public_path), str(public_digest), str(adopted_path), str(adopted_digest)) for identifier, public_path, public_digest, adopted_path, adopted_digest in expected}


def validate_current_identifier_collisions(
    public_ids: dict[str, tuple[str, str, str]],
    adopted_ids: dict[str, tuple[str, str, str]],
    collision_records: dict[str, tuple[str, str, str, str]],
) -> None:
    for identifier, expected in sorted(collision_records.items()):
        if identifier not in public_ids or identifier not in adopted_ids:
            raise ValueError(f"recorded current identifier collision is absent: {identifier}")
        public = public_ids[identifier]
        adopted = adopted_ids[identifier]
        if (public[0], public[2], adopted[0], adopted[2]) != expected:
            raise ValueError(f"recorded current identifier collision bytes drift: {identifier}")
    for identifier in sorted(set(public_ids) & set(adopted_ids)):
        public = public_ids[identifier]
        adopted = adopted_ids[identifier]
        if public[2] == adopted[2]:
            continue
        observed = (public[0], public[2], adopted[0], adopted[2])
        if collision_records.get(identifier) != observed:
            raise ValueError(f"duplicate canonical identifier with different current-source bytes: {identifier}")


def validate_inventory(public_root: Path, adopted_root: Path, inventory: dict[str, Any] | None = None) -> dict[str, Counter[str]]:
    inventory = load_inventory() if inventory is None else inventory
    if git(public_root, "merge-base", "--is-ancestor", str(inventory["publicSourceBase"]), "HEAD") != "":
        raise ValueError("public source does not contain the pinned corrected base")
    adopted_commit = str(inventory["adoptedMainAtAudit"])
    git(adopted_root, "cat-file", "-e", f"{adopted_commit}^{{commit}}")
    collision_records = validate_collision_receipt(inventory, public_root, adopted_root)
    scans = {"public": (public_root, None, public_paths(public_root)), "adopted": (adopted_root, adopted_commit, adopted_paths(adopted_root, adopted_commit))}
    ids: dict[str, dict[str, tuple[str, str, str]]] = {}
    counts: dict[str, Counter[str]] = {}
    for name, (root, commit, paths) in scans.items():
        config = inventory["repositories"][name]
        if list(config.get("exclusions") or []) != [".github/"]:
            raise ValueError(f"discovery exclusions drift: {name}")
        entries: list[tuple[str, str]] = []
        count: Counter[str] = Counter()
        for path in paths:
            if not path.endswith(STRUCTURED_SUFFIXES):
                continue
            surface = classify_path(path, list(config["rules"]), list(config["exclusions"]))
            if surface == "excluded":
                continue
            count[surface] += 1
            count[f"{surface}:{path_subrole(path)}"] += 1
            entries.append((path, surface))
            if VERSION_PATH.search(path):
                count[f"{surface}:path"] += 1
            if path.endswith(".json"):
                document = load_json_bytes(bytes_for(name, root, commit, path), f"{name}:{path}")
                for _, key, _ in walk_json(document):
                    if key in IDENTIFIER_ROLES:
                        count[f"{surface}:{IDENTIFIER_ROLES[key]}"] += 1
                    version_role = version_field_role(key, surface)
                    if version_role is not None:
                        surface_for_field, role = version_role
                        count[f"{surface_for_field}:{role}"] += 1
            else:
                for line in bytes_for(name, root, commit, path).decode("utf-8").splitlines():
                    match = YAML_KEY.match(line)
                    if not match:
                        continue
                    key = match.group(1)
                    if key in IDENTIFIER_ROLES:
                        count[f"{surface}:{IDENTIFIER_ROLES[key]}"] += 1
                    version_role = version_field_role(key, surface)
                    if version_role is not None:
                        surface_for_field, role = version_role
                        count[f"{surface_for_field}:{role}"] += 1
        ids[name] = schema_ids(name, root, commit, entries)
        counts[name] = count
    validate_aliases(inventory, public_root)
    validate_current_identifier_collisions(ids["public"], ids["adopted"], collision_records)
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check version-bearing structured identifiers across public and adopted sources.")
    parser.add_argument("--adopted-repo", type=Path, default=os.environ.get("CRINKL_PROTOCOL_ADOPTED_REPO"), help="Git repository containing the adopted audit pin; CRINKL_PROTOCOL_ADOPTED_REPO is an optional fallback.")
    parser.add_argument("--report", action="store_true", help="Print deterministic repository/surface counts.")
    args = parser.parse_args()
    if args.adopted_repo is None:
        parser.error("--adopted-repo or CRINKL_PROTOCOL_ADOPTED_REPO is required")
    return args


def main() -> int:
    args = parse_args()
    try:
        counts = validate_inventory(ROOT, args.adopted_repo.resolve())
    except ValueError as exc:
        print(f"[identifier-inventory] {exc}", file=sys.stderr)
        return 1
    for repository in sorted(counts):
        rendered = ", ".join(f"{key}={counts[repository][key]}" for key in sorted(counts[repository]))
        print(f"[identifier-inventory] {repository}: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
