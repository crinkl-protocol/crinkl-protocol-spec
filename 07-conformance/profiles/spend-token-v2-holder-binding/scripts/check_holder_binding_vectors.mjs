#!/usr/bin/env node

import {
  createHash,
  createPrivateKey,
  createPublicKey,
  sign,
  verify
} from "node:crypto";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const vectorUrl = new URL(
  "../conformance/v2/vectors/token.spendAttestation.holderBinding.v2.json",
  import.meta.url
);
const vector = JSON.parse(await readFile(vectorUrl, "utf8"));

const assert = (condition, message) => {
  if (!condition) throw new Error(message);
};
const sha256 = (bytes) => createHash("sha256").update(bytes).digest();
const hashId = (bytes) => `sha256:${sha256(bytes).toString("hex")}`;
assert(
  vector.kind === "token.spendAttestation.holderBinding.v2",
  "unexpected vector kind"
);

function canonicalize(value) {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("non-finite JSON number");
    return Object.is(value, -0) ? "0" : String(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  if (typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`)
      .join(",")}}`;
  }
  throw new TypeError(`unsupported JSON value: ${typeof value}`);
}

function holderCommitment(spendId, publicKeyBytes) {
  return hashId(
    Buffer.concat([
      Buffer.from(vector.constants.holderCommitmentDomainUtf8, "utf8"),
      Buffer.from(spendId, "utf8"),
      publicKeyBytes
    ])
  );
}

function rawPublicKey(publicKeyBase64) {
  const decoded = Buffer.from(publicKeyBase64, "base64");
  assert(decoded.length === 32, "holder public key must decode to 32 bytes");
  assert(
    decoded.toString("base64") === publicKeyBase64,
    "public key must use canonical base64"
  );
  return decoded;
}

const valid = vector.valid;
assert(
  valid.expectedDecision?.accepted === true &&
    valid.expectedDecision?.code === "holder_control_verified",
  "valid decision changed"
);
const publicKeyBytes = rawPublicKey(vector.keyMaterial.holderPublicKeyBase64);
assert(
  holderCommitment(valid.spendId, publicKeyBytes) ===
    valid.expectedHolderCommitment,
  "holder commitment mismatch"
);

const tokenCanonical = canonicalize(valid.unsignedToken);
assert(
  tokenCanonical === valid.expectedTokenCanonical,
  "token canonicalization mismatch"
);
assert(
  hashId(Buffer.from(tokenCanonical, "utf8")) === valid.expectedSpendTokenHash,
  "Spend token hash mismatch"
);
assert(
  valid.issuerSignature.tokenHashHex ===
    valid.expectedSpendTokenHash.slice("sha256:".length),
  "issuer token hash does not match expected Spend token hash"
);

const pkcs8Prefix = Buffer.from("302e020100300506032b657004220420", "hex");
const spkiPrefix = Buffer.from("302a300506032b6570032100", "hex");
const issuerPrivateKey = createPrivateKey({
  key: Buffer.concat([
    pkcs8Prefix,
    Buffer.from(vector.issuerKeyMaterial.privateKeySeedHex, "hex")
  ]),
  format: "der",
  type: "pkcs8"
});
const issuerDigest = Buffer.from(valid.issuerSignature.tokenHashHex, "hex");
assert(
  sign(null, issuerDigest, issuerPrivateKey).toString("base64") ===
    valid.issuerSignature.signatureBase64,
  "deterministic issuer signature mismatch"
);
const issuerPublicKeyBytes = rawPublicKey(
  vector.issuerKeyMaterial.publicKeyBase64
);
assert(
  valid.issuerSignature.publicKeyBase64 ===
    vector.issuerKeyMaterial.publicKeyBase64,
  "issuer signature public key mismatch"
);
const issuerPublicKey = createPublicKey({
  key: Buffer.concat([spkiPrefix, issuerPublicKeyBytes]),
  format: "der",
  type: "spki"
});
assert(
  verify(
    null,
    issuerDigest,
    issuerPublicKey,
    Buffer.from(valid.issuerSignature.signatureBase64, "base64")
  ),
  "valid issuer signature rejected"
);

const challengeCanonical = canonicalize(valid.challenge);
assert(
  challengeCanonical === valid.expectedChallengeCanonical,
  "challenge canonicalization mismatch"
);
const challengeDigest = sha256(Buffer.from(challengeCanonical, "utf8"));
assert(
  `sha256:${challengeDigest.toString("hex")}` === valid.expectedChallengeId,
  "challengeId mismatch"
);

const privateKey = createPrivateKey({
  key: Buffer.concat([
    pkcs8Prefix,
    Buffer.from(vector.keyMaterial.privateKeySeedHex, "hex")
  ]),
  format: "der",
  type: "pkcs8"
});
assert(
  sign(null, challengeDigest, privateKey).toString("base64") ===
    valid.holderProof.signatureBase64,
  "deterministic holder signature mismatch"
);

const publicKey = createPublicKey({
  key: Buffer.concat([spkiPrefix, publicKeyBytes]),
  format: "der",
  type: "spki"
});
assert(
  verify(
    null,
    challengeDigest,
    publicKey,
    Buffer.from(valid.holderProof.signatureBase64, "base64")
  ),
  "valid holder signature rejected"
);

const issuedAt = Date.parse(valid.challenge.issuedAt);
const expiresAt = Date.parse(valid.challenge.expiresAt);
const verificationTime = Date.parse(valid.verificationTime);
assert(
  valid.challenge.domain === vector.constants.challengeDomain &&
    valid.challenge.schemaVersion === 2,
  "challenge domain or schema mismatch"
);
assert(
  vector.constants.signatureInput === "RAW_SHA256_CHALLENGE_DIGEST_BYTES",
  "signature input profile changed"
);
const nonceBytes = Buffer.from(valid.challenge.nonceBase64, "base64");
assert(
  nonceBytes.length === 32 &&
    nonceBytes.toString("base64") === valid.challenge.nonceBase64,
  "challenge nonce must decode to 32 bytes"
);
assert(
  [
    "TOKEN_PRESENTATION",
    "CAMPAIGN_PROOF_AUTHORIZATION",
    "CAMPAIGN_ACTION_AUTHORIZATION"
  ].includes(valid.challenge.purpose),
  "unsupported challenge purpose"
);
assert(
  valid.challenge.spendTokenHash === valid.expectedSpendTokenHash &&
    valid.holderProof.spendTokenHash === valid.challenge.spendTokenHash &&
    valid.holderProof.scopeId === valid.challenge.scopeId &&
    /^sha256:[0-9a-f]{64}$/.test(valid.challenge.requestContextHash) &&
    valid.holderProof.challengeId === valid.expectedChallengeId,
  "holder proof binding mismatch"
);
assert(
  expiresAt > issuedAt &&
    expiresAt - issuedAt <=
      vector.constants.maximumChallengeLifetimeSeconds * 1000,
  "invalid challenge lifetime"
);
assert(
  verificationTime >= issuedAt && verificationTime < expiresAt,
  "valid vector is outside challenge lifetime"
);
assert(
  valid.challengePreviouslyConsumed === false,
  "valid vector challenge unexpectedly consumed"
);

const wrongKey = rawPublicKey(vector.keyMaterial.wrongPublicKeyBase64);
assert(
  holderCommitment(valid.spendId, wrongKey) !== valid.expectedHolderCommitment,
  "wrong key unexpectedly matches holder commitment"
);

const badSignature = Buffer.from(valid.holderProof.signatureBase64, "base64");
badSignature[0] ^= 1;
assert(
  !verify(null, challengeDigest, publicKey, badSignature),
  "mutated holder signature unexpectedly verified"
);

const changedScopeChallenge = structuredClone(valid.challenge);
changedScopeChallenge.scopeId =
  "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
assert(
  hashId(Buffer.from(canonicalize(changedScopeChallenge), "utf8")) !==
    valid.holderProof.challengeId,
  "changed scope unexpectedly retained challengeId"
);
const changedRequestChallenge = structuredClone(valid.challenge);
changedRequestChallenge.requestContextHash =
  "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
assert(
  hashId(Buffer.from(canonicalize(changedRequestChallenge), "utf8")) !==
    valid.holderProof.challengeId,
  "changed request context unexpectedly retained challengeId"
);
assert(
  Date.parse("2026-07-28T00:05:00.000Z") >= expiresAt,
  "expired vector boundary is not expired"
);

const withoutBinding = structuredClone(valid.unsignedToken);
delete withoutBinding.holderBinding;
assert(
  withoutBinding.schemaVersion === 2 && !("holderBinding" in withoutBinding),
  "absent holderBinding vector is malformed"
);

const expectedNegativeCodes = new Map([
  ["holder-binding-wrong-key", "holder_commitment_mismatch"],
  ["holder-binding-wrong-signature", "holder_signature_invalid"],
  ["holder-binding-changed-scope", "holder_challenge_id_mismatch"],
  ["holder-binding-changed-request", "holder_challenge_id_mismatch"],
  ["holder-binding-expired", "holder_challenge_expired"],
  ["holder-binding-replayed", "holder_challenge_replayed"]
]);
for (const testCase of vector.negativeCases) {
  if (testCase.id === "holder-binding-absent") {
    assert(
      testCase.expectedTokenDecision?.code === "spend_token_valid" &&
        testCase.expectedHolderDecision?.code === "holder_control_unavailable",
      "absent-binding decisions changed"
    );
    continue;
  }
  assert(
    testCase.expectedDecision?.code === expectedNegativeCodes.get(testCase.id),
    `unexpected decision for ${testCase.id}`
  );
}
assert(
  vector.negativeCases.length === expectedNegativeCodes.size + 1,
  "negative case count changed"
);
console.log(
  JSON.stringify({
    ok: true,
    vector: fileURLToPath(vectorUrl),
    validCases: 1,
    negativeCases: vector.negativeCases.length,
    challengeId: valid.expectedChallengeId,
    spendTokenHash: valid.expectedSpendTokenHash
  })
);
