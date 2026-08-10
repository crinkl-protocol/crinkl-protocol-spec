#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const vectorUrl = new URL(
  "../conformance/spend-attestation-portability/v1/vectors/spend-attestation.zk-commitment-geography.v1.json",
  import.meta.url
);
const manifestUrl = new URL("../manifest.json", import.meta.url);
const spendTokenDocUrl = new URL("../../../../protocol/portability/spend-attestation-token.md", import.meta.url);
const verifierDocUrl = new URL("../../../../protocol/portability/verifier-requirements.md", import.meta.url);
const zkDocUrl = new URL("../../../../protocol/extensions/zk-proof-extension.md", import.meta.url);
const releaseUrl = new URL("../../../../versions/release.json", import.meta.url);
const suiteManifestUrl = new URL("../../../vectors/v1/manifest.json", import.meta.url);

const [vectorBytes, manifestBytes, spendTokenDoc, verifierDoc, zkDoc, releaseBytes, suiteManifestBytes] = await Promise.all([
  readFile(vectorUrl),
  readFile(manifestUrl),
  readFile(spendTokenDocUrl, "utf8"),
  readFile(verifierDocUrl, "utf8"),
  readFile(zkDocUrl, "utf8"),
  readFile(releaseUrl),
  readFile(suiteManifestUrl)
]);
const vector = JSON.parse(vectorBytes);
const manifest = JSON.parse(manifestBytes);
const release = JSON.parse(releaseBytes);
const suiteManifest = JSON.parse(suiteManifestBytes);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(
  vector.kind === "token.spendAttestation.portableV1.zkCommitmentGeography",
  "unexpected vector kind"
);
assert(
  JSON.stringify(vector.constants.requiredCommitments) ===
    JSON.stringify(["C_store", "C_total", "C_dayIndex"]),
  "unexpected required commitment labels"
);
assert(
  JSON.stringify(vector.constants.optionalCommitments) ===
    JSON.stringify(["C_currency", "C_geoRegion", "C_cbsaCode"]),
  "unexpected optional commitment labels"
);
assert(
  JSON.stringify(vector.constants.privacyOmittedCanonicalFields) ===
    JSON.stringify(["geoRegion", "cbsaCode"]),
  "unexpected privacy-omitted canonical fields"
);

const vectorArtifact = manifest.artifacts.find(
  (artifact) => artifact.file.endsWith("spend-attestation.zk-commitment-geography.v1.json")
);
assert(vectorArtifact, "manifest does not bind the geography vector");
assert(
  createHash("sha256").update(vectorBytes).digest("hex") === vectorArtifact.sha256,
  "geography vector hash does not match manifest"
);
const releasedRc7Boundary =
  release.releaseVersion === "1.0.0-rc.7" &&
  release.status === "RELEASED" &&
  suiteManifest.releaseVersion === "1.0.0-rc.7" &&
  suiteManifest.suiteVersion === 4;
const unpublishedRc8Boundary =
  release.releaseVersion === "1.0.0-rc.8" &&
  release.status === "RELEASE_CANDIDATE_NOT_PUBLISHED" &&
  suiteManifest.releaseVersion === "1.0.0-rc.8" &&
  suiteManifest.suiteVersion === 5;
assert(
  releasedRc7Boundary || unpublishedRc8Boundary,
  "public-package release/candidate boundary drift"
);
assert(manifest.publicRepositoryVersion === "1.0.0-rc.7", "geography public repository version drift");
assert(
  JSON.stringify(manifest.engineeringSource) ===
    JSON.stringify({
      repository: "crinkl-protocol",
      commit: "52648bae72a8c3b83883392be1c4ae714e4359c3",
      maturity: "engineering-adopted-on-protected-main"
    }),
  "geography engineering source anchor drift"
);
assert(manifest.conformanceManifestEntry.status === "PRESENT_IN_RC7_SUITE_4_SOURCE_CANDIDATE", "geography suite status drift");
assert(suiteManifest.vectors.some((entry) => entry.kind === vector.kind), "current suite manifest omits geography profile");
assert(suiteManifest.vectors.some((entry) => entry.kind === "token.spendAttestation.holderBinding.v2"), "current suite manifest omits retained holder-binding profile");

function evaluate(caseDefinition) {
  const token = caseDefinition.token;
  if (
    !token ||
    token.tokenType !== "SPEND_ATTESTATION" ||
    (token.schemaVersion !== 1 && token.schemaVersion !== 2) ||
    !token.canonical ||
    typeof token.canonical !== "object"
  ) {
    return "invalid_token_shape";
  }
  if (caseDefinition.profile === "legacy-signed-token") return "accepted";
  if (caseDefinition.profile !== "privacy-preserving-portable") return "unknown_profile";
  const commitments = token.zk?.commitments;
  if (!commitments || typeof commitments !== "object") return "missing_required_commitment";
  if (!vector.constants.requiredCommitments.every((label) => Object.hasOwn(commitments, label))) {
    return "missing_required_commitment";
  }
  if (Object.hasOwn(token.canonical, "geoRegion") || Object.hasOwn(token.canonical, "cbsaCode")) {
    return "plaintext_geography_forbidden";
  }
  return "accepted";
}

for (const positiveCase of vector.positiveCases) {
  assert(evaluate(positiveCase) === "accepted", `${positiveCase.id} was not accepted`);
}
for (const rejectCase of vector.rejectCases) {
  assert(
    evaluate(rejectCase) === rejectCase.expectedCode,
    `${rejectCase.id} produced the wrong result`
  );
}

assert(
  spendTokenDoc.includes("C_currency`, `C_geoRegion`, and `C_cbsaCode` are independently OPTIONAL"),
  "Spend Token doc does not state optional geography commitments"
);
assert(
  spendTokenDoc.includes("Privacy-preserving portable issuance (normative)"),
  "Spend Token doc does not state the privacy-preserving issuance rule"
);
assert(
  zkDoc.includes("C_geoRegion?: Commitment") && zkDoc.includes("C_cbsaCode?: Commitment"),
  "ZK extension does not mark geography commitments optional"
);
assert(
  verifierDoc.includes("does not independently prove that the underlying physical purchase occurred"),
  "verifier requirements overstate the purchase claim"
);

console.log(
  `spend-token geography commitments: ${vector.positiveCases.length} accepted, ` +
    `${vector.rejectCases.length} rejected; docs aligned`
);
