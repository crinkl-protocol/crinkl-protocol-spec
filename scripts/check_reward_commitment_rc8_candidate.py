#!/usr/bin/env python3
"""Verify the unreviewed rc.8 reward-commitment public-spec candidate."""
from __future__ import annotations

import hashlib
import json
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "8ed9b6314c88728de325c2905589f5d84e502379"
BASE_TREE = "c7ac02cadcdd2fa662c521ab1599ea3fbb2d9215"
ADOPTED = "093b37db3e78bdd4253d7864ae4eb5398ce7cc25"
RC7 = "d45560e679c12298ee25fad6e0e7948b03e5a7c5"
ADOPTED_TREE = "d4cb3a9af00c3bc55134ccdb342e7a806400c2e9"
ADOPTED_ARTIFACTS = {
    "protocol/portability/TOKENS.md": "sha256:e094a25cb91ba43053c7deeb8299c7e544268a6155a5d7e83ab324eac694df34",
    "protocol/portability/COMMITMENT_LAYER.md": "sha256:fcea079a78df09808b0ec11e26819481d404a9df8d1058c0136889b46a6ab2b7",
    "conformance/reward-commitment-presentation/v1/vectors/two-token.v1.json": "sha256:375ad582c4d014de7ccb96b332843da8b2522e6bafaff232671ba5b062fc3c1a",
    "conformance/reward-commitment-presentation/v1/manifest.json": "sha256:1f2196201f2902ad8ad4948ac4206a442a5d624b724daa1945391bfa65b03811",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip())
    return result.stdout.strip()


def tag_exists(tag: str) -> bool:
    result = subprocess.run(["git", "-C", str(ROOT), "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"], check=False)
    require(result.returncode in (0, 1), f"cannot inspect tag {tag}")
    return result.returncode == 0


def digest(path: str) -> str:
    return "sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def adopted_blob_digest(adopted_root: Path, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(adopted_root), "show", f"{ADOPTED}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return "sha256:" + hashlib.sha256(result.stdout).hexdigest()


def adopted_git(adopted_root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(adopted_root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip())
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adopted-repo", type=Path, required=True, help="checkout containing the adopted crinkl-protocol candidate")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        adopted_root = args.adopted_repo.resolve()
        require((adopted_root / ".git").exists(), "--adopted-repo is not a Git checkout")
        release = json.loads((ROOT / "versions/release.json").read_text())
        registry = json.loads((ROOT / "versions/release-registry.json").read_text())
        manifest = json.loads((ROOT / "07-conformance/vectors/v1/manifest.json").read_text())
        plan = json.loads((ROOT / "versions/v1.0.0-rc.8/finalization.json").read_text())
        require(release.get("releaseVersion") == "1.0.0-rc.8" and release.get("requiredTag") == "v1.0.0-rc.8" and release.get("status") == "RELEASE_CANDIDATE_NOT_PUBLISHED", "release candidate state")
        require(registry.get("latestReleasedVersion") == "1.0.0-rc.7" and registry.get("candidateState") == "SOURCE_CANDIDATE_AWAITING_REVIEW_NOT_PUBLISHABLE", "registry state")
        require(registry.get("reviewedCandidateVersion") is None, "rc.8 is unreviewed and must leave reviewedCandidateVersion null")
        require(manifest.get("releaseVersion") == "1.0.0-rc.8" and manifest.get("suiteVersion") == 5 and manifest.get("releaseStatus") == release.get("status"), "suite manifest state")
        require(git("rev-parse", "v1.0.0-rc.7^{commit}") == RC7, "rc.7 immutable tag")
        require(git("rev-parse", f"{BASE}^{{tree}}") == BASE_TREE, "public base tree")
        source = plan.get("sourceComposition", {})
        require(source.get("publicSpecBase") == {"commit": BASE, "tree": BASE_TREE}, "public base pin")
        require(source.get("adoptedCandidate") == {"repository": "crinkl-protocol", "commit": ADOPTED, "tree": ADOPTED_TREE}, "adopted candidate pin")
        require(adopted_git(adopted_root, "rev-parse", f"{ADOPTED}^{{tree}}") == ADOPTED_TREE, "adopted candidate tree")
        for path, expected_digest in ADOPTED_ARTIFACTS.items():
            require(adopted_blob_digest(adopted_root, path) == expected_digest, f"adopted artifact digest: {path}")
        require(plan.get("releaseVersion") == "1.0.0-rc.8" and plan.get("latestReleasedVersion") == "1.0.0-rc.7" and plan.get("candidateState") == "SOURCE_CANDIDATE_AWAITING_REVIEW_NOT_PUBLISHABLE", "finalization identity")
        require(not tag_exists("v1.0.0-rc.8"), "rc.8 tag must be absent")
        controlling = {item.get("path"): item.get("sha256") for item in plan.get("controllingArtifacts", []) if isinstance(item, dict)}
        for path in (
            "protocol/portability/spend-attestation-token.md",
            "protocol/applications/economics/settlement-bindings.md",
            "07-conformance/compatibility.md",
            "versions/CHANGELOG.md",
        ):
            require(path in controlling, f"missing controlling artifact: {path}")
        for item in plan.get("controllingArtifacts", []):
            require(isinstance(item, dict) and item.get("sha256") == digest(item["path"]), f"artifact digest mismatch: {item.get('path')}")
        print("[reward-commitment-rc8] OK (unreviewed suite-5 candidate; rc.7 remains immutable)")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"[reward-commitment-rc8] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
