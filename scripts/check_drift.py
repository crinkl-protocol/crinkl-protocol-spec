#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def die(msg: str) -> int:
    eprint(f"[drift-check] {msg}")
    return 1


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(read_text(path))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def iter_protocol_version_consts(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        if "protocolVersion" in node and isinstance(node["protocolVersion"], dict) and isinstance(node["protocolVersion"].get("const"), str):
            yield node["protocolVersion"]["const"]
        for v in node.values():
            yield from iter_protocol_version_consts(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_protocol_version_consts(v)


def subject_to_event_name(subject: str) -> str | None:
    if subject.startswith("event."):
        return subject[len("event.") :].upper()
    if subject.startswith("system."):
        return subject[len("system.") :].upper()
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    binding_dir = repo_root / "bindings" / "nats" / "crinkl-platform" / "v1"
    protocol_binding_path = binding_dir / "binding.protocol.yaml"
    platform_binding_path = binding_dir / "binding.platform.yaml"

    if not protocol_binding_path.exists():
        return die(f"missing {protocol_binding_path}")
    if not platform_binding_path.exists():
        return die(f"missing {platform_binding_path}")

    protocol_binding = read_yaml(protocol_binding_path)
    platform_binding = read_yaml(platform_binding_path)

    protocol_version = str(protocol_binding.get("protocolVersion") or "")
    platform_version = str(platform_binding.get("protocolVersion") or "")
    if not protocol_version:
        return die(f"binding.protocol.yaml missing protocolVersion: {protocol_binding_path}")
    if protocol_version != platform_version:
        return die(f"binding protocolVersion mismatch: protocol={protocol_version}, platform={platform_version}")

    protocol_subjects: dict[str, str] = dict(protocol_binding.get("subjects") or {})
    platform_subjects: dict[str, str] = dict(platform_binding.get("subjects") or {})

    for key, subj in protocol_subjects.items():
        if subj.startswith("pipeline."):
            return die(f"protocol binding contains pipeline subject: {key}={subj}")
        if subj == "event.deadletter":
            return die(f"protocol binding contains DLQ subject: {key}={subj}")
        if not (subj.startswith("event.") or subj.startswith("system.")):
            return die(f"protocol binding contains non-protocol subject: {key}={subj}")

    for key, subj in platform_subjects.items():
        if subj == "event.deadletter":
            continue
        if subj.startswith("pipeline."):
            continue
        return die(f"platform binding contains non-platform subject: {key}={subj}")

    for binding_name, binding in [("protocol", protocol_binding), ("platform", platform_binding)]:
        subjects: dict[str, str] = dict(binding.get("subjects") or {})
        streams: dict[str, Any] = dict(binding.get("streams") or {})
        subject_schemas: dict[str, str] = dict(binding.get("subjectSchemas") or {})

        for stream_key, stream in streams.items():
            for subject_key in stream.get("subjects") or []:
                if subject_key not in subjects:
                    return die(f"{binding_name} binding stream '{stream_key}' references unknown subject key: {subject_key}")

        for subject_key, rel_schema_path in subject_schemas.items():
            if subject_key not in subjects:
                return die(f"{binding_name} binding has schema for unknown subject key: {subject_key}")
            schema_path = binding_dir / rel_schema_path
            if not schema_path.exists():
                return die(f"{binding_name} binding references missing schema: {schema_path}")

            schema = read_json(schema_path)
            if not schema.get("$id"):
                return die(f"schema missing $id: {schema_path}")

            consts = set(iter_protocol_version_consts(schema))
            if consts and consts != {protocol_version}:
                return die(f"schema protocolVersion const mismatch in {schema_path}: {sorted(consts)} (expected {protocol_version})")

    # Reward scalar encoding: deltaPoints/deltaBTCsats must be string-encoded integers.
    for fname in ["event.reward_provisional_issued.schema.json", "event.reward_final_issued.schema.json"]:
        schema = read_json(binding_dir / "schemas" / fname)
        payload_props = (((schema.get("properties") or {}).get("payload") or {}).get("properties") or {})
        for field in ["deltaPoints", "deltaBTCsats"]:
            spec = payload_props.get(field) or {}
            if spec.get("type") != "string":
                return die(f"{fname} payload.{field} must be type=string")

    # Repository release and wire protocol versions are separate surfaces.
    release = read_json(repo_root / "versions" / "release.json")
    release_version = str(release.get("releaseVersion") or "")
    release_status = str(release.get("status") or "")
    if not release_version:
        return die("versions/release.json missing releaseVersion")
    if release_status not in {"RELEASE_CANDIDATE_NOT_PUBLISHED", "RELEASED"}:
        return die(f"versions/release.json invalid status: {release_status}")
    if release.get("requiredTag") != f"v{release_version}":
        return die("versions/release.json requiredTag must equal v + releaseVersion")
    if release.get("defaultBindingProtocolVersion") != protocol_version:
        return die(
            "release/default binding mismatch: "
            f"release={release.get('defaultBindingProtocolVersion')} binding={protocol_version}"
        )
    supported_wire_versions = list(release.get("supportedWireProtocolVersions") or [])
    if len(supported_wire_versions) != len(set(supported_wire_versions)):
        return die("versions/release.json supportedWireProtocolVersions contains duplicates")
    if protocol_version not in supported_wire_versions:
        return die("default binding protocolVersion is not in supportedWireProtocolVersions")
    release_snapshot = repo_root / "versions" / f"v{release_version}" / "snapshot.md"
    if not release_snapshot.is_file():
        return die(f"missing release snapshot: {release_snapshot}")
    if release_status not in read_text(release_snapshot):
        return die("release snapshot does not declare the release manifest status")

    # Spec/docs release-version consistency.
    readme = read_text(repo_root / "README.md")
    m = re.search(r"\*\*v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\*\*", readme)
    if not m:
        return die("README.md missing version marker '**vX.Y.Z**'")
    if m.group(1) != release_version:
        return die(
            f"README.md release mismatch: README={m.group(1)} release={release_version}"
        )

    evolution = read_text(repo_root / "08-governance" / "versioning.md")
    m2 = re.search(
        r"Current public repository (source candidate|release):\s+"
        r"\*\*(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\*\*",
        evolution,
    )
    if not m2:
        return die(
            "08-governance/versioning.md missing "
            "'Current public repository source candidate|release: **X.Y.Z**'"
        )
    expected_versioning_label = (
        "release" if release_status == "RELEASED" else "source candidate"
    )
    if m2.group(1) != expected_versioning_label:
        return die(
            "versioning.md release-state label mismatch: "
            f"versioning={m2.group(1)} expected={expected_versioning_label}"
        )
    if m2.group(2) != release_version:
        return die(
            f"versioning.md release mismatch: versioning={m2.group(2)} release={release_version}"
        )

    # spend-event.md must mention every bound protocol/system event name.
    events_md = read_text(repo_root / "01-core" / "spend-event.md")
    bound_event_names = {
        subject_to_event_name(v)
        for v in protocol_subjects.values()
        if subject_to_event_name(v) is not None
    }
    present = set(re.findall(r"\|\s*([A-Z0-9_]+)\s*\|", events_md))
    missing = sorted([n for n in bound_event_names if n and n not in present])
    if missing:
        return die(f"01-core/spend-event.md missing event(s): {', '.join(missing)}")

    # 01-core/schemas/event.schema.json must cover all spend-stream event names.
    ref_schema = read_json(repo_root / "01-core" / "schemas" / "event.schema.json")
    ref_enum = set(((ref_schema.get("properties") or {}).get("eventName") or {}).get("enum") or [])
    spend_names = {subject_to_event_name(v) for v in protocol_subjects.values() if v.startswith("event.")}
    spend_missing = sorted([n for n in spend_names if n and n not in ref_enum])
    if spend_missing:
        return die(f"01-core/schemas/event.schema.json missing eventName enum(s): {', '.join(spend_missing)}")

    # Conformance manifest version must match the binding (catches half-applied version bumps).
    manifest = read_json(repo_root / "07-conformance" / "vectors" / "v1" / "manifest.json")
    mver = manifest.get("protocolVersion")
    if mver != protocol_version:
        return die(f"07-conformance manifest version mismatch: manifest={mver} binding={protocol_version}")
    if manifest.get("releaseVersion") != release_version:
        return die("07-conformance manifest releaseVersion mismatch")
    if manifest.get("releaseStatus") != release_status:
        return die("07-conformance manifest releaseStatus mismatch")
    if manifest.get("supportedWireProtocolVersions") != supported_wire_versions:
        return die("07-conformance manifest supportedWireProtocolVersions mismatch")
    release_conformance = dict(release.get("conformance") or {})
    if manifest.get("suite") != release_conformance.get("suite"):
        return die("07-conformance manifest suite mismatch with release manifest")
    if manifest.get("suiteVersion") != release_conformance.get("suiteVersion"):
        return die("07-conformance manifest suiteVersion mismatch with release manifest")

    successor_finalizer = repo_root / "scripts" / "check_successor_release_finalization.py"
    if not successor_finalizer.is_file():
        return die("missing successor release finalization verifier")
    finalizer_mode = "released" if release_status == "RELEASED" else "candidate"
    if subprocess.run([sys.executable, str(successor_finalizer), "--mode", finalizer_mode], cwd=repo_root).returncode != 0:
        return die("successor release finalization verifier failed")

    # The optional W3C VC profile follows the active candidate/released state.
    # Its verifier proves adopted-source bytes, the rc.4 immutable baseline,
    # rc.5 suite inclusion, official self-cell boundaries, and fixture checks.
    w3c_bundle_checker = (
        repo_root
        / "07-conformance"
        / "profiles"
        / "w3c-vc-2.0-spend-attestation-v1"
        / "scripts"
        / "check_w3c_vc_2_0_spend_attestation_bundle.py"
    )
    if not w3c_bundle_checker.is_file():
        return die("missing W3C VC candidate bundle verifier")
    if subprocess.run([sys.executable, str(w3c_bundle_checker)], cwd=repo_root).returncode != 0:
        return die("W3C VC candidate bundle verifier failed")

    # Leak guard: this PUBLIC repo must not contain internal/private-tagged content.
    leaked = [
        str(md.relative_to(repo_root))
        for md in repo_root.rglob("*.md")
        if re.search(r"(?m)^\s*visibility:\s*(internal|private)\b", read_text(md))
    ]
    if leaked:
        return die(f"leak guard: internal/private content present in PUBLIC spec: {', '.join(leaked[:8])}")

    print(
        "[drift-check] OK "
        f"(release={release_version}/{release_status}, "
        f"defaultProtocolVersion={protocol_version}, manifest+leak-guard clean)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
