#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_pointer_parts(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def pointer_get(document: Any, pointer: str) -> Any:
    current = document
    for part in json_pointer_parts(pointer):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def pointer_set(document: Any, pointer: str, value: Any) -> None:
    parts = json_pointer_parts(pointer)
    current = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    final = parts[-1]
    if isinstance(current, list):
        current[int(final)] = value
    else:
        current[final] = value


def rendered_json_sha256(document: dict[str, Any]) -> str:
    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def check_documentation(repo_root: Path, plan: dict[str, Any], mode: str) -> None:
    for transition in plan.get("documentationTransitions") or []:
        path = repo_root / str(transition["path"])
        text = path.read_text(encoding="utf-8")
        required = str(transition["candidateMarker" if mode == "candidate" else "releasedMarker"])
        forbidden = str(transition["releasedMarker" if mode == "candidate" else "candidateMarker"])
        if text.count(required) != 1:
            raise ValueError(f"{mode} documentation marker count mismatch: {path}")
        if forbidden in text:
            raise ValueError(f"opposite release-state marker present: {path}")


def check_tag(repo_root: Path, required_tag: str) -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, text=True, capture_output=True
    ).stdout.strip()
    tagged = subprocess.run(
        ["git", "rev-parse", f"refs/tags/{required_tag}^{{commit}}"],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if tagged != head:
        raise ValueError(f"release tag does not identify HEAD: tag={tagged} head={head}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("candidate", "released"), default="candidate")
    parser.add_argument("--require-tag", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    plan = read_json(repo_root / "versions" / "v1.0.0-rc.3" / "finalization.json")
    if plan.get("kind") != "crinkl.protocol.releaseFinalizationPlanV1":
        raise ValueError("release finalization plan kind drift")
    if plan.get("releaseVersion") != "1.0.0-rc.3":
        raise ValueError("release finalization version drift")
    if plan.get("requiredTag") != "v1.0.0-rc.3":
        raise ValueError("release finalization tag drift")
    if plan.get("requiredProductionAuthorization") != "PRODUCTION-OPS OK":
        raise ValueError("release production authorization boundary drift")

    documents: dict[str, dict[str, Any]] = {}
    for transition in plan.get("machineTransitions") or []:
        relative = str(transition["path"])
        document = documents.setdefault(relative, read_json(repo_root / relative))
        expected = transition[args.mode]
        if pointer_get(document, str(transition["pointer"])) != expected:
            raise ValueError(
                f"{args.mode} machine transition mismatch: {relative}{transition['pointer']}"
            )

    check_documentation(repo_root, plan, args.mode)

    if args.mode == "candidate":
        simulated = copy.deepcopy(documents)
        for transition in plan.get("machineTransitions") or []:
            pointer_set(
                simulated[str(transition["path"])],
                str(transition["pointer"]),
                transition["released"],
            )
        file_hashes = {
            path: rendered_json_sha256(document)
            for path, document in sorted(simulated.items())
        }
        identity = {
            "releaseVersion": plan["releaseVersion"],
            "requiredTag": plan["requiredTag"],
            "engineeringSource": plan["engineeringSource"],
            "machineFileSha256": file_hashes,
        }
        identity_digest = hashlib.sha256(
            json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
                "utf-8"
            )
        ).hexdigest()
        print(
            "[rc3-release-finalization] OK "
            f"(candidate; simulatedReleaseIdentity=sha256:{identity_digest})"
        )
    else:
        if args.require_tag:
            check_tag(repo_root, str(plan["requiredTag"]))
        print(
            "[rc3-release-finalization] OK "
            f"(released; tagRequired={str(args.require_tag).lower()})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
