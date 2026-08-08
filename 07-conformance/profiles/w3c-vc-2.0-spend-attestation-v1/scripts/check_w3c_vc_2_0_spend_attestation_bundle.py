#!/usr/bin/env python3
"""Fail-closed verifier for the candidate public W3C Spend Attestation bundle."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


EXPECTED_ARTIFACTS = {
    "protocol/W3C_VC_2_0_BINDING.md",
    "protocol/context/spend-v1.jsonld",
    "protocol/schemas/spend_attestation_credential_v1.schema.json",
    "protocol/schemas/w3c_bitstring_status_list_credential_v1.schema.json",
    "protocol/schemas/w3c_issuer_key_history_v1.schema.json",
    "conformance/spend-attestation-portability/v1/vectors/spend-attestation.wallet-omitted.v1.json",
    "conformance/w3c-vc-2.0/v1/README.md",
    "conformance/w3c-vc-2.0/v1/manifest.json",
    "conformance/w3c-vc-2.0/v1/validate_draft202012.py",
    "conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-refresh-clear.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-refresh-set.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-revocation-clear.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-revocation-set.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/did-web-vc-test.example.json",
    "conformance/w3c-vc-2.0/v1/fixtures/issuer-history-trust-root.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-bootstrap.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-current.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-status-current.v1.json",
    "conformance/w3c-vc-2.0/v1/fixtures/status-list-resolution.v1.json",
    "conformance/w3c-vc-2.0/v1/vectors/bitstring-status-list-credential.v1.json",
    "conformance/w3c-vc-2.0/v1/vectors/spend-attestation-credential.v1.json",
    "conformance/w3c-vc-2.0/v1/official-suite/execution-evidence.json",
    "conformance/w3c-vc-2.0/v1/official-suite/manifest.json",
    "scripts/check_w3c_spend_attestation_credential_vectors.mjs",
    "scripts/check_w3c_bitstring_status_list_vectors.mjs",
    "scripts/generate_w3c_bitstring_status_list_vectors.mjs",
}

PUBLIC_FRONTMATTER = "---\nstatus: draft\nlayer: portability\nversion: v1\nnormative: true\n---\n\n"
W3C_KIND = "credential.spendAttestation.vcdm2.eddsaJcs2022"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise ValueError(message)


def run(bundle_root: Path, *command: str) -> None:
    subprocess.run(command, cwd=bundle_root, check=True)


def all_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in all_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in all_strings(child)]
    return []


def main() -> int:
    bundle_root = Path(__file__).resolve().parents[1]
    repo_root = bundle_root.parents[2]
    manifest = load_json(bundle_root / "manifest.json")
    release = load_json(repo_root / "versions/release.json")
    release_status = release.get("status")
    if release.get("releaseVersion") != "1.0.0-rc.5" or release_status not in {"RELEASE_CANDIDATE_NOT_PUBLISHED", "RELEASED"}:
        fail("rc.5 release boundary drift")
    released = release_status == "RELEASED"
    expected_bundle_state = {
        "maturity": "released" if released else "candidate",
        "releasedConformance": released,
        "conformanceStatus": "PRESENT_IN_RELEASED_RC5_SUITE_3" if released else "PRESENT_IN_RC5_SUITE_3_SOURCE_CANDIDATE",
        "publicationBlockers": [] if released else ["P4.4_EXACT_PUBLIC_CANDIDATE_REVIEW", "P9_ACCEPTED_PUBLIC_RELEASE"],
        "releaseClaim": released,
    }
    if manifest.get("maturity") != expected_bundle_state["maturity"] or manifest.get("releasedConformance") is not expected_bundle_state["releasedConformance"]:
        fail("W3C profile maturity boundary drift")
    if manifest.get("engineeringSource") != {
        "repository": "crinkl-protocol",
        "commit": "ae6382f1ed11b88f9bbfdcc4ef12119647cc7698",
        "maturity": "engineering-adopted-on-protected-main",
    }:
        fail("engineering source anchor drift")
    if manifest.get("publicRepositoryVersion") != "1.0.0-rc.5":
        fail("candidate public-version boundary drift")
    if manifest.get("conformanceManifestEntry") != {
        "kind": W3C_KIND,
        "file": "../../profiles/w3c-vc-2.0-spend-attestation-v1/conformance/w3c-vc-2.0/v1/vectors/spend-attestation-credential.v1.json",
        "externalVerifier": {
            "type": "node",
            "file": "../../profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_spend_attestation_credential_vectors.mjs",
        },
        "status": expected_bundle_state["conformanceStatus"],
    }:
        fail("W3C conformance entry drift")
    if manifest.get("publicationBlockers") != expected_bundle_state["publicationBlockers"]:
        fail("publication blockers drift")
    expected_claims = {
        "completeOfficialW3CTestSuite": False, "peerInteroperability": False,
        "genericVcVpApi": False, "runtime": False, "release": expected_bundle_state["releaseClaim"], "production": False,
    }
    if manifest.get("claims") != expected_claims:
        fail("claim boundary drift")
    expected_launch = {
        "DID_WEB_ENDPOINT_PUBLICATION", "IMMUTABLE_CONTEXT_ENDPOINT_PUBLICATION",
        "SIGNED_STATUS_LIST_ENDPOINT_PUBLICATION", "SPEND_HEAD_REFRESH_ENDPOINT_PUBLICATION",
        "RUNTIME_ADOPTION", "QA", "PRODUCTION_AUTHORITY",
    }
    if set(manifest.get("launchBlockers") or []) != expected_launch:
        fail("launch blockers drift")
    artifacts = manifest.get("artifacts") or []
    artifact_paths = [entry.get("file") for entry in artifacts]
    if len(artifact_paths) != len(set(artifact_paths)) or set(artifact_paths) != EXPECTED_ARTIFACTS:
        fail("artifact inventory is not the exact required adopted set")
    bundle_files = {
        path.relative_to(bundle_root).as_posix()
        for path in bundle_root.rglob("*")
        if path.is_file()
    }
    expected_bundle_files = EXPECTED_ARTIFACTS | {
        "README.md",
        "manifest.json",
        "scripts/check_w3c_vc_2_0_spend_attestation_bundle.py",
    }
    if bundle_files != expected_bundle_files:
        fail(f"unexpected bundle file inventory: {sorted(bundle_files ^ expected_bundle_files)}")
    for entry in artifacts:
        source_path = entry.get("sourcePath")
        file_path = entry.get("file")
        if source_path != file_path or not isinstance(file_path, str):
            fail("artifact source-path mapping drift")
        artifact = bundle_root / file_path
        if not artifact.is_file():
            fail(f"missing bundled artifact: {file_path}")
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual != entry.get("sha256"):
            fail(f"artifact hash drift: {file_path}")

    adopted_binding = (bundle_root / "protocol/W3C_VC_2_0_BINDING.md").read_text(encoding="utf-8")
    public_binding = (repo_root / "03-portability/w3c-vc-2.0-binding.md").read_text(encoding="utf-8")
    if public_binding != PUBLIC_FRONTMATTER + adopted_binding:
        fail("public binding is not the controlled-frontmatter transform of adopted binding")

    current_manifest = load_json(repo_root / "07-conformance/vectors/v1/manifest.json")
    expected_entry = {
        "kind": W3C_KIND,
        "file": "../../profiles/w3c-vc-2.0-spend-attestation-v1/conformance/w3c-vc-2.0/v1/vectors/spend-attestation-credential.v1.json",
        "externalVerifier": {
            "type": "node",
            "file": "../../profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_spend_attestation_credential_vectors.mjs",
        },
    }
    if current_manifest.get("releaseVersion") != "1.0.0-rc.5" or current_manifest.get("releaseStatus") != release_status or current_manifest.get("suiteVersion") != 3:
        fail("rc.5 candidate suite boundary drift")
    if sum(entry == expected_entry for entry in current_manifest.get("vectors") or []) != 1:
        fail("rc.5 candidate suite must contain exactly one manifest-bound W3C entry")
    frozen_rc4 = subprocess.run(
        ["git", "show", "v1.0.0-rc.4:07-conformance/vectors/v1/manifest.json"],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.encode("utf-8")
    if hashlib.sha256(frozen_rc4).hexdigest() != "4deb342629d0c85f34b06cedf9c0e006dc2016d14fad53e301507ff2beeb06cd":
        fail("immutable rc.4 manifest hash drift")
    released_manifest = json.loads(frozen_rc4)
    if released_manifest.get("releaseVersion") != "1.0.0-rc.4" or released_manifest.get("releaseStatus") != "RELEASED" or released_manifest.get("suiteVersion") != 2 or W3C_KIND in all_strings(released_manifest):
        fail("immutable rc.4 suite baseline drift")

    official_manifest = load_json(bundle_root / "conformance/w3c-vc-2.0/v1/official-suite/manifest.json")
    evidence = load_json(bundle_root / "conformance/w3c-vc-2.0/v1/official-suite/execution-evidence.json")
    profile_manifest = load_json(bundle_root / "conformance/w3c-vc-2.0/v1/manifest.json")
    expected_official = manifest.get("officialSelfCellEvidence")
    if expected_official != {
        "file": "conformance/w3c-vc-2.0/v1/official-suite/execution-evidence.json",
        "rowsPassed": 32, "rowsPending": 8, "completeOfficialSuiteClaimed": False,
        "peerInteroperabilityClaimed": False, "runtimeBindingAuthorized": False,
    }:
        fail("bundle official-self-cell declaration drift")
    if evidence.get("officialRowsPassed") != 32 or evidence.get("officialRowsPending") != 8:
        fail("official evidence row counts drift")
    if evidence.get("results", {}).get("eddsaJcs2022", {}).get("passing") != 13:
        fail("EdDSA self-cell evidence drift")
    bsl = evidence.get("results", {}).get("bitstringStatusList", {})
    if bsl.get("passing") != 19 or bsl.get("pending") != 8 or not bsl.get("pendingReason"):
        fail("Bitstring Status List self-cell evidence drift")
    for key in ("peerInteroperabilityClaimed", "genericVcApiProductCapabilityClaimed", "fullOfficialSuiteConformanceClaimed", "runtimeBindingAuthorized"):
        if evidence.get(key) is not False:
            fail(f"official evidence overclaims {key}")
    if evidence.get("protocolBaseCommit") != official_manifest.get("protocolBaseCommit"):
        fail("official evidence source commit drift")
    if evidence.get("adapterSourceSnapshot", {}).get("commit") != "f8b35316105948a67e52df6470ae585091f2d9e2":
        fail("official adapter source snapshot drift")
    if evidence.get("directStatusProbes") != {
        "clearAccepted": True,
        "setRejected": True,
        "tamperedStatusProofRejected": True,
    }:
        fail("official status-aware probe evidence drift")
    if official_manifest.get("officialRowsExecuted") != 32 or official_manifest.get("officialRowsPending") != 8:
        fail("official manifest counts drift")
    if official_manifest.get("localTraceabilityAssertionCount") != 58:
        fail("official traceability assertion count drift")
    if official_manifest.get("officialSuiteConformanceClaimed") is not False or official_manifest.get("peerInteroperabilityClaimed") is not False or official_manifest.get("genericVcApiCapabilityClaimed") is not False or official_manifest.get("runtimeBindingAuthorized") is not False:
        fail("official manifest overclaims capability")
    if profile_manifest.get("applicableOfficialSelfCellEvidence") != "official-suite/execution-evidence.json" or profile_manifest.get("applicableOfficialSelfCellRowsPassed") != 32 or profile_manifest.get("applicableOfficialSelfCellRowsPending") != 8 or profile_manifest.get("applicableOfficialSelfCellClaimed") is not True:
        fail("profile manifest official self-cell linkage drift")
    if profile_manifest.get("officialW3CTestSuiteClaimed") is not False or profile_manifest.get("peerInteroperabilityClaimed") is not False or profile_manifest.get("genericVcApiCapabilityClaimed") is not False or profile_manifest.get("runtimeBindingAuthorized") is not False:
        fail("profile manifest overclaims capability")

    run(bundle_root, "node", "scripts/check_w3c_spend_attestation_credential_vectors.mjs")
    run(bundle_root, "node", "scripts/generate_w3c_bitstring_status_list_vectors.mjs")
    run(bundle_root, "node", "scripts/check_w3c_bitstring_status_list_vectors.mjs")
    run(bundle_root, "python3", "conformance/w3c-vc-2.0/v1/validate_draft202012.py", "--check")
    for entry in artifacts:
        actual = hashlib.sha256((bundle_root / entry["file"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            fail(f"checker mutated adopted artifact: {entry['file']}")
    print(f"[w3c-profile-bundle] OK ({len(artifacts)} adopted artifacts; official self-cell 32 passed, 8 pending)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"[w3c-profile-bundle] {error}", file=sys.stderr)
        raise SystemExit(1)
