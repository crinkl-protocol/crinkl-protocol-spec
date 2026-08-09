#!/usr/bin/env python3
"""Verify the public protocol release registry against immutable Git evidence.

Pinned adopted-protocol commits require --adopted-repo so their existence is
independently checked. The optional --baseline enforces append-only semantics
for registered maps and designated ordered observation lists. It compares
parsed JSON values, so whitespace and object-member order are not history.
New entries remain subject to every ordinary registry check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class DuplicateKeyError(ValueError):
    pass


SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

KNOWN_COLLISION_RECEIPT = {
    "algorithm": "sha256",
    "digest": "sha256:0d1c6a393a9be65bbb1d33a36e5e06b92708a352b351790120ceccc3e1ac5ac6",
    "lineCount": 22,
    "state": "OBSERVED_UNRESOLVED_RELEASED_IDENTITY_COLLISION",
    "comparisons": [
        {
            "publicTag": "v1.0.0-rc.3",
            "publicCommit": "a8368577b6331ed5c076105da1536e32be39bdf6",
            "adoptedCommit": "8c641f57201c75bac12819a0f903ae6105c7f3c3",
        },
        {
            "publicTag": "v1.0.0-rc.4",
            "publicCommit": "7ce390fb3f562f589318ea36e9b8200aa4585da0",
            "adoptedCommit": "5019e41bdeb924449363aa3b538eaa5b3b6ee4dc",
        },
    ],
}


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON object key: {key!r}")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def git(root: Path, *args: str, binary: bool = False) -> bytes | str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        return None
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def tag_ref_exists(root: Path, tag: str) -> bool:
    """Return whether a local tag ref exists, failing closed on Git errors."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ValueError(f"cannot inspect local tag ref {tag}: {exc}") from exc
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.decode("utf-8", errors="replace").strip()
    raise ValueError(f"cannot inspect local tag ref {tag}: {detail or f'git exited {result.returncode}'}")


def semver_parts(value: str) -> tuple[tuple[int, int, int], list[str]] | None:
    match = SEMVER.fullmatch(value)
    if not match:
        return None
    core = tuple(int(match.group(index)) for index in range(1, 4))
    prerelease = match.group(4).split(".") if match.group(4) else []
    return core, prerelease


def compare_semver(left: str, right: str) -> int:
    parsed_left = semver_parts(left)
    parsed_right = semver_parts(right)
    if parsed_left is None or parsed_right is None:
        raise ValueError(f"invalid SemVer comparison: {left!r}, {right!r}")
    left_core, left_pre = parsed_left
    right_core, right_pre = parsed_right
    if left_core != right_core:
        return -1 if left_core < right_core else 1
    if not left_pre or not right_pre:
        if left_pre == right_pre:
            return 0
        return -1 if left_pre else 1
    for left_part, right_part in zip(left_pre, right_pre):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            return -1 if int(left_part) < int(right_part) else 1
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return -1 if left_part < right_part else 1
    if len(left_pre) == len(right_pre):
        return 0
    return -1 if len(left_pre) < len(right_pre) else 1


def maximum_semver(versions: list[str]) -> str | None:
    if not versions:
        return None
    maximum = versions[0]
    for candidate in versions[1:]:
        if compare_semver(candidate, maximum) > 0:
            maximum = candidate
    return maximum


def error(errors: list[str], location: str, message: str) -> None:
    errors.append(f"{location}: {message}")


def validate_schema(schema: dict[str, Any], registry: Any) -> list[str]:
    errors: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes several schema-error types.
        return [f"schema: {exc}"]
    validator = Draft202012Validator(schema)
    for item in sorted(validator.iter_errors(registry), key=lambda entry: (list(entry.path), entry.message)):
        path = "/".join(str(part) for part in item.path) or "$"
        error(errors, f"schema:{path}", item.message)
    return errors


def source_matches(root: Path, source: Any, location: str, errors: list[str]) -> None:
    if not isinstance(source, dict):
        return
    commit = source.get("commit")
    tree = source.get("tree")
    if not isinstance(commit, str) or not isinstance(tree, str):
        return
    if git(root, "cat-file", "-e", f"{commit}^{{commit}}") is None:
        error(errors, location, f"source commit does not exist: {commit}")
        return
    observed = git(root, "rev-parse", f"{commit}^{{tree}}")
    if observed != tree:
        error(errors, location, f"source tree mismatch: expected {tree}, observed {observed}")


def adopted_repo_usable(root: Path | None) -> bool:
    return root is not None and git(root, "rev-parse", "--is-inside-work-tree") == "true"


def adopted_source_matches(root: Path | None, source: Any, location: str, errors: list[str]) -> None:
    if not isinstance(source, dict):
        return
    commit = source.get("commit")
    if not isinstance(commit, str):
        return
    if not adopted_repo_usable(root):
        error(errors, location, "pinned adopted source requires a usable --adopted-repo")
        return
    assert root is not None
    if git(root, "cat-file", "-e", f"{commit}^{{commit}}") is None:
        error(errors, location, f"adopted source commit does not exist: {commit}")
        return
    tree = source.get("tree")
    if isinstance(tree, str):
        observed_tree = git(root, "rev-parse", f"{commit}^{{tree}}")
        if observed_tree != tree:
            error(errors, location, f"adopted source tree mismatch: expected {tree}, observed {observed_tree}")
    artifacts = source.get("artifactInventory")
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            verify_artifact_blob(root, commit, artifact, f"{location}.artifactInventory[{index}]", errors)


def artifact_key(artifact: Any) -> tuple[Any, Any, Any, Any, Any]:
    if not isinstance(artifact, dict):
        return (None, None, None, None, None)
    return (
        artifact.get("path"),
        artifact.get("digestAlgorithm"),
        artifact.get("digestBasis"),
        artifact.get("digest"),
        artifact.get("role"),
    )


def verify_artifact_blob(root: Path, commit: str, artifact: Any, location: str, errors: list[str]) -> None:
    if not isinstance(artifact, dict):
        return
    path = artifact.get("path")
    digest = artifact.get("digest")
    if not isinstance(path, str) or not isinstance(digest, str):
        return
    blob = git(root, "cat-file", "blob", f"{commit}:{path}", binary=True)
    if blob is None:
        error(errors, location, f"artifact is absent from {commit}: {path}")
        return
    observed = "sha256:" + hashlib.sha256(blob).hexdigest()
    if observed != digest:
        error(errors, location, f"exact Git blob digest mismatch for {path}: expected {digest}, observed {observed}")


def expected_release_tuple(record: dict[str, Any]) -> tuple[str, str, str, str] | None:
    status = record.get("status")
    manifest = record.get("releaseManifestArtifact")
    conformance = record.get("conformance")
    if status == "RELEASED" and manifest is not None and conformance is not None:
        authority = record.get("authority", {})
        if authority.get("manifestAuthority") == "AUTHORITY_ACCEPTED":
            return ("PRESENT_IMMUTABLE_TAG", "AUTHORITY_ACCEPTED", "ACCEPTED_TAG_AND_MANIFEST", "COMPLETE")
        return ("PRESENT_IMMUTABLE_TAG", "COMPUTED_NOT_AUTHORITY_ACCEPTED", "RELEASED_TAG_WITH_UNACCEPTED_MANIFEST", "INCOMPLETE")
    if status == "RELEASED" and manifest is None and conformance is None:
        return ("PRESENT_IMMUTABLE_TAG", "NOT_AVAILABLE_LEGACY", "LEGACY_RELEASED_TAG_PROVENANCE_INCOMPLETE", "INCOMPLETE")
    if status == "REVIEWED_CANDIDATE_NOT_PUBLISHED":
        return ("NOT_CREATED", "COMPUTED_NOT_AUTHORITY_ACCEPTED", "REVIEWED_SOURCE_NOT_RELEASED", "INCOMPLETE")
    return None


def validate_release(
    root: Path,
    version: str,
    record: Any,
    releases: dict[str, Any],
    errors: list[str],
) -> None:
    location = f"releases[{version}]"
    if not isinstance(record, dict):
        return
    source = record.get("source")
    source_matches(root, source, f"{location}.source", errors)
    expected_tag = f"v{version}"
    if record.get("plannedTag") != expected_tag:
        error(errors, location, f"plannedTag must equal {expected_tag}")
    status = record.get("status")
    actual_tag = record.get("actualTag")
    if status == "RELEASED":
        if actual_tag != expected_tag:
            error(errors, location, f"released actualTag must equal {expected_tag}")
    elif status == "REVIEWED_CANDIDATE_NOT_PUBLISHED":
        if actual_tag is not None:
            error(errors, location, "reviewed unpublished candidate must not have an actualTag")
        try:
            if tag_ref_exists(root, expected_tag):
                error(errors, location, f"reviewed unpublished candidate must not have a plannedTag ref: {expected_tag}")
        except ValueError as exc:
            error(errors, location, str(exc))
    previous = record.get("previousRelease")
    if previous is not None:
        if previous not in releases:
            error(errors, location, f"previousRelease does not resolve: {previous}")
        else:
            try:
                if compare_semver(previous, version) >= 0:
                    error(errors, location, f"previousRelease is not semantically older: {previous}")
            except ValueError as exc:
                error(errors, location, str(exc))
    authority = record.get("authority")
    tuple_expected = expected_release_tuple(record)
    if not isinstance(authority, dict) or tuple_expected is None:
        error(errors, location, "status/manifest authority tuple is not recognized")
    else:
        observed = (
            authority.get("tagState"),
            authority.get("manifestAuthority"),
            authority.get("releaseAuthority"),
            authority.get("provenanceCompleteness"),
        )
        if observed != tuple_expected:
            error(errors, location, f"authority tuple mismatch: expected {tuple_expected}, observed {observed}")
    if isinstance(actual_tag, str) and isinstance(source, dict):
        commit = source.get("commit")
        tree = source.get("tree")
        tag_commit = git(root, "rev-parse", f"refs/tags/{actual_tag}^{{commit}}")
        tag_tree = git(root, "rev-parse", f"refs/tags/{actual_tag}^{{tree}}")
        if tag_commit != commit or tag_tree != tree:
            error(errors, location, f"actual tag does not resolve to recorded source commit/tree: {actual_tag}")
    inventory = record.get("artifactInventory")
    if not isinstance(inventory, list) or not isinstance(source, dict):
        return
    manifest = record.get("releaseManifestArtifact")
    conformance = record.get("conformance")
    required_artifacts: list[tuple[str, dict[str, Any]]] = []
    if isinstance(manifest, dict):
        required_artifacts.append(("releaseManifestArtifact", manifest))
    if isinstance(conformance, dict):
        required_artifacts.append((
            "conformance",
            {
                "path": conformance.get("manifest"),
                "digestAlgorithm": "sha256",
                "digestBasis": "EXACT_GIT_BLOB_BYTES",
                "digest": conformance.get("manifestDigest"),
                "role": "CONFORMANCE_MANIFEST",
            },
        ))
    for name, artifact in required_artifacts:
        same_path_role = [entry for entry in inventory if isinstance(entry, dict) and entry.get("path") == artifact.get("path") and entry.get("role") == artifact.get("role")]
        if len(same_path_role) != 1 or artifact_key(same_path_role[0]) != artifact_key(artifact):
            error(errors, location, f"{name} must appear exactly once in artifactInventory with matching path, digest, role, and basis")
    commit = source.get("commit")
    if isinstance(commit, str):
        for index, artifact in enumerate(inventory):
            verify_artifact_blob(root, commit, artifact, f"{location}.artifactInventory[{index}]", errors)


def validate_predecessors(releases: dict[str, Any], errors: list[str]) -> None:
    for start in releases:
        seen: set[str] = set()
        current = start
        while current is not None:
            if current in seen:
                error(errors, f"releases[{start}]", f"predecessor cycle includes {current}")
                break
            seen.add(current)
            record = releases.get(current)
            current = record.get("previousRelease") if isinstance(record, dict) else None


def validate_profiles(
    registry: dict[str, Any],
    release_manifest: Any,
    adopted_root: Path | None,
    errors: list[str],
) -> None:
    profiles = registry.get("profiles")
    if not isinstance(profiles, dict):
        return
    for key, profile in profiles.items():
        location = f"profiles[{key}]"
        if not isinstance(profile, dict):
            continue
        maturity = profile.get("maturity")
        document = profile.get("documentMaturity")
        authority = profile.get("authorityState")
        source_state = profile.get("adoptedSourceState")
        source = profile.get("adoptedSource")
        if maturity == "RELEASED":
            if (document, authority, source_state) != ("RELEASED", "RELEASED_TAG_ACCEPTED", "PINNED"):
                error(errors, location, "released maturity requires released document, released-tag authority, and pinned adopted source")
        elif maturity == "CANDIDATE":
            if document != "CANDIDATE":
                error(errors, location, "candidate maturity requires candidate document maturity")
            if authority == "CANDIDATE_SOURCE_ONLY" and source_state != "PINNED":
                error(errors, location, "candidate-source authority requires a pinned adopted source")
            if authority == "PUBLIC_SPEC_CANDIDATE_WITHOUT_ADOPTED_SOURCE" and source_state != "NOT_CLAIMED":
                error(errors, location, "public-only candidate authority requires no adopted source")
        if source_state == "PINNED" and not isinstance(source, dict):
            error(errors, location, "pinned adoptedSourceState requires an adoptedSource")
        if source_state == "NOT_CLAIMED" and source is not None:
            error(errors, location, "not-claimed adoptedSourceState requires null adoptedSource")
        if isinstance(source, dict):
            adopted_source_matches(adopted_root, source, f"{location}.adoptedSource", errors)
        runtime = profile.get("runtimeSupport")
        if runtime not in {"UNAVAILABLE", "SEPARATELY_GOVERNED"}:
            error(errors, location, f"runtimeSupport is not a non-activation state: {runtime}")
        constraints = profile.get("objectConstraints")
        if not isinstance(constraints, list):
            continue
        object_ids: set[str] = set()
        for index, constraint in enumerate(constraints):
            if not isinstance(constraint, dict):
                continue
            object_id = constraint.get("objectId")
            if not isinstance(object_id, str):
                continue
            if object_id in object_ids:
                error(errors, f"{location}.objectConstraints[{index}]", f"duplicate objectId within profile: {object_id}")
            object_ids.add(object_id)
            supported = constraint.get("supportedSchemaVersions")
            required = constraint.get("requiredSchemaVersions")
            if isinstance(supported, list) and isinstance(required, list) and not set(required).issubset(supported):
                error(errors, f"{location}.objectConstraints[{index}]", "requiredSchemaVersions must be a subset of supportedSchemaVersions")
    if not isinstance(release_manifest, dict):
        return
    manifest_profiles = release_manifest.get("profiles")
    if not isinstance(manifest_profiles, list):
        error(errors, "versions/release.json", "profiles must be an array")
        return
    manifest_kinds: set[str] = set()
    for index, entry in enumerate(manifest_profiles):
        if not isinstance(entry, dict):
            error(errors, f"versions/release.json.profiles[{index}]", "profile entry must be an object")
            continue
        kind = entry.get("kind")
        if isinstance(kind, str):
            if kind in manifest_kinds:
                error(errors, f"versions/release.json.profiles[{index}]", f"duplicate profile kind: {kind}")
            manifest_kinds.add(kind)
        registered = profiles.get(kind)
        if not isinstance(kind, str) or not isinstance(registered, dict):
            error(errors, f"versions/release.json.profiles[{index}]", f"unregistered profile kind: {kind}")
            continue
        if entry.get("maturity") != registered.get("maturity"):
            error(errors, f"versions/release.json.profiles[{index}]", "maturity differs from registry")
        if entry.get("runtimeAvailability") != registered.get("runtimeSupport"):
            error(errors, f"versions/release.json.profiles[{index}]", "runtime availability differs from registry")


def validate_baseline(current: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for section in ("releases", "profiles", "embeddedWireVersionObservations"):
        prior = baseline.get(section)
        latest = current.get(section)
        if not isinstance(prior, dict) or not isinstance(latest, dict):
            error(errors, f"baseline.{section}", "both baseline and current registries must contain an object")
            continue
        for key, prior_value in prior.items():
            if key not in latest:
                error(errors, f"baseline.{section}[{key}]", "registered entry was deleted")
            elif latest[key] != prior_value:
                error(errors, f"baseline.{section}[{key}]", "registered entry was mutated")
    if current.get("releasedSchemaIdentityCollisionReceipt") != baseline.get("releasedSchemaIdentityCollisionReceipt"):
        error(errors, "baseline.releasedSchemaIdentityCollisionReceipt", "known collision receipt was mutated or deleted")
    if current.get("ledgerVersion") != baseline.get("ledgerVersion"):
        error(errors, "baseline.ledgerVersion", "ledger version was mutated")
    for section in ("additionalCollisionObservations", "unassignedSourceHeads"):
        prior = baseline.get(section)
        latest = current.get(section)
        if not isinstance(prior, list) or not isinstance(latest, list):
            error(errors, f"baseline.{section}", "both baseline and current registries must contain an array")
        elif len(latest) < len(prior) or latest[:len(prior)] != prior:
            error(errors, f"baseline.{section}", "existing ordered observations must remain an exact prefix")
    return errors


def validate_registry(
    root: Path,
    schema: dict[str, Any],
    registry: Any,
    release_manifest: Any,
    adopted_root: Path | None = None,
) -> list[str]:
    errors = validate_schema(schema, registry)
    if not isinstance(registry, dict):
        return errors
    releases = registry.get("releases")
    if not isinstance(releases, dict):
        return errors
    latest = registry.get("latestReleasedVersion")
    latest_record = releases.get(latest)
    if not isinstance(latest_record, dict) or latest_record.get("status") != "RELEASED":
        error(errors, "latestReleasedVersion", "must resolve to a RELEASED entry")
    released_versions = [version for version, record in releases.items() if isinstance(record, dict) and record.get("status") == "RELEASED"]
    maximum_released = maximum_semver(released_versions)
    if maximum_released is not None and latest != maximum_released:
        error(errors, "latestReleasedVersion", f"must equal SemVer-maximum RELEASED version: {maximum_released}")
    reviewed = registry.get("reviewedCandidateVersion")
    if reviewed is not None:
        reviewed_record = releases.get(reviewed)
        if not isinstance(reviewed_record, dict) or reviewed_record.get("status") != "REVIEWED_CANDIDATE_NOT_PUBLISHED":
            error(errors, "reviewedCandidateVersion", "must resolve to REVIEWED_CANDIDATE_NOT_PUBLISHED or be null")
    reviewed_versions = [version for version, record in releases.items() if isinstance(record, dict) and record.get("status") == "REVIEWED_CANDIDATE_NOT_PUBLISHED"]
    maximum_reviewed = maximum_semver(reviewed_versions)
    if reviewed is not None and reviewed != maximum_reviewed:
        error(errors, "reviewedCandidateVersion", f"must equal SemVer-maximum reviewed candidate: {maximum_reviewed}")
    if reviewed is not None and isinstance(latest, str):
        try:
            if compare_semver(reviewed, latest) <= 0:
                error(errors, "reviewedCandidateVersion", "must be later than latestReleasedVersion")
        except ValueError as exc:
            error(errors, "reviewedCandidateVersion", str(exc))
    if registry.get("candidateState") == "NO_ACTIVE_OR_PUBLISHABLE_CANDIDATE":
        for version, record in releases.items():
            if isinstance(record, dict) and record.get("status") == "REVIEWED_CANDIDATE_NOT_PUBLISHED" and record.get("actualTag") is not None:
                error(errors, f"releases[{version}]", "no-active candidate state forbids an actual tag")
    for version, record in releases.items():
        validate_release(root, version, record, releases, errors)
        if isinstance(record, dict):
            for index, source in enumerate(record.get("adoptedSources", [])):
                adopted_source_matches(adopted_root, source, f"releases[{version}].adoptedSources[{index}]", errors)
    validate_predecessors(releases, errors)
    for index, head in enumerate(registry.get("unassignedSourceHeads", [])):
        if isinstance(head, dict):
            source_matches(root, head.get("source"), f"unassignedSourceHeads[{index}].source", errors)
    if registry.get("releasedSchemaIdentityCollisionReceipt") != KNOWN_COLLISION_RECEIPT:
        error(errors, "releasedSchemaIdentityCollisionReceipt", "does not match the immutable known collision receipt")
    validate_profiles(registry, release_manifest, adopted_root, errors)
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the protocol release registry against public and adopted Git evidence.",
        epilog=(
            "--adopted-repo is required when the registry pins adopted commits. --baseline permits map additions but rejects "
            "deletion or parsed-value mutation of existing releases, profiles, embedded-wire observations, ledgerVersion, and "
            "the known collision receipt; additional collision observations and unassigned heads retain an exact prefix."
        ),
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--registry", default="versions/release-registry.json")
    parser.add_argument("--schema", default="versions/release-ledger.schema.json")
    parser.add_argument("--release-manifest", default="versions/release.json")
    parser.add_argument("--adopted-repo", type=Path, help="Git checkout containing every pinned crinkl-protocol commit.")
    parser.add_argument("--baseline", type=Path, help="Prior registry whose existing entries must remain unchanged.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    try:
        schema = load_json(resolve(root, args.schema))
        registry = load_json(resolve(root, args.registry))
        release_manifest = load_json(resolve(root, args.release_manifest))
        adopted_root = args.adopted_repo.resolve() if args.adopted_repo else None
        errors = validate_registry(root, schema, registry, release_manifest, adopted_root)
        if args.baseline:
            baseline = load_json(resolve(root, args.baseline))
            errors.extend(validate_schema(schema, baseline))
            if isinstance(registry, dict) and isinstance(baseline, dict):
                errors.extend(validate_baseline(registry, baseline))
    except ValueError as exc:
        errors = [str(exc)]
    if errors:
        print("[release-registry] FAIL", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("[release-registry] OK (schema, registry, public/adopted Git evidence, and profile consistency)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
