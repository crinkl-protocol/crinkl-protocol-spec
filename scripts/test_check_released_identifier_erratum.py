#!/usr/bin/env python3
"""Focused hostile tests for the released identifier-collision erratum gate."""
from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path

import check_released_identifier_erratum as checker

ROOT = Path(__file__).resolve().parents[1]

def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adopted-repo", type=Path, default=os.environ.get("CRINKL_PROTOCOL_ADOPTED_REPO"))
    parsed = parser.parse_args()
    if parsed.adopted_repo is None:
        parser.error("--adopted-repo or CRINKL_PROTOCOL_ADOPTED_REPO is required")
    return parsed

def rejected(name: str, document: dict, adopted: Path | None = None) -> None:
    try:
        checker.validate_local(ROOT, document)
        if adopted is not None:
            checker.validate_full(ROOT, adopted, document)
    except ValueError:
        print(f"[released-identifier-erratum-test] rejected: {name}")
        return
    raise AssertionError(f"{name}: mutation was accepted")

def main() -> int:
    adopted = args().adopted_repo.resolve()
    _, document = checker.read_document(ROOT, checker.ERRATUM_REL)
    checker.validate_local(ROOT, document)
    checker.validate_full(ROOT, adopted, document)
    checker.validate_docs(ROOT)
    print("[released-identifier-erratum-test] accepted: current erratum")
    for name, mutate in [
        ("missing mapping", lambda value: value["mappings"].pop()),
        ("duplicate old identifier", lambda value: value["mappings"].append(copy.deepcopy(value["mappings"][0]))),
        ("unsorted mappings", lambda value: value["mappings"].reverse()),
        ("wrong successor digest", lambda value: value["mappings"][0]["successor"].__setitem__("sha256", "sha256:" + "0" * 64)),
        ("wrong successor identifier", lambda value: value["mappings"][0]["successor"].__setitem__("identifier", "crinkl://wrong/successor")),
        ("wrong old public digest", lambda value: value["mappings"][0]["oldPublic"].__setitem__("sha256", "sha256:" + "0" * 64)),
        ("wrong receipt", lambda value: value["effectiveCollisionReceipt"].__setitem__("digest", "sha256:" + "0" * 64)),
        ("wrong tag pin", lambda value: value["releasedTagPins"][0].__setitem__("commit", "0" * 40)),
        ("wrong public inventory artifact commit", lambda value: value["publicInventory"].__setitem__("artifactCommit", "0" * 40)),
        ("wrong successor source commit", lambda value: value["successorSourceMap"].__setitem__("commit", "0" * 40)),
        ("wrong successor source state", lambda value: value["successorSourceMap"].__setitem__("state", "MUTATED")),
        ("inactive migration removed", lambda value: value["standing"].__setitem__("consumerMigration", "ACTIVE")),
    ]:
        mutated = copy.deepcopy(document)
        mutate(mutated)
        rejected(name, mutated, adopted if name == "wrong successor digest" else None)
    try:
        checker.load_json(b'{"mappings":[],"mappings":[]}', "duplicate-key fixture")
    except ValueError:
        print("[released-identifier-erratum-test] rejected: duplicate JSON key")
    else:
        raise AssertionError("duplicate JSON key was accepted")
    try:
        checker.load_json(b'{"mappings":', "malformed fixture")
    except ValueError:
        print("[released-identifier-erratum-test] rejected: malformed JSON")
    else:
        raise AssertionError("malformed JSON was accepted")
    original_git = checker.git
    def reject_head(root: Path, *git_args: str) -> bytes:
        if any(arg == "HEAD" or arg.startswith("HEAD:") for arg in git_args):
            raise AssertionError("checker must not read adopted HEAD")
        return original_git(root, *git_args)
    checker.git = reject_head
    try:
        checker.validate_full(ROOT, adopted, document)
    finally:
        checker.git = original_git
    print("[released-identifier-erratum-test] accepted: exact Git object path ignores adopted HEAD")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
