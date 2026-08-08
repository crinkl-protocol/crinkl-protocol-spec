#!/usr/bin/env node

import { createHash, createPrivateKey, createPublicKey, sign } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const fixturesRoot = new URL("conformance/w3c-vc-2.0/v1/fixtures/", root);
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));
const vector = await readJson("conformance/w3c-vc-2.0/v1/vectors/bitstring-status-list-credential.v1.json");
const spendVector = await readJson("conformance/w3c-vc-2.0/v1/vectors/spend-attestation-credential.v1.json");
const currentHistory = await readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-current.v1.json");
const existingTrustRoot = await readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-history-trust-root.v1.json");
const existingDid = await readJson("conformance/w3c-vc-2.0/v1/fixtures/did-web-vc-test.example.json");

const base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const sha256 = (value) => createHash("sha256").update(value).digest();
const jsonBytes = (value) => `${JSON.stringify(value, null, 2)}\n`;

function hasLoneSurrogate(value) {
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!Number.isInteger(next) || next < 0xdc00 || next > 0xdfff) return true;
      index += 1;
    } else if (code >= 0xdc00 && code <= 0xdfff) return true;
  }
  return false;
}

function canonicalize(value) {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("non-finite JSON number");
    return JSON.stringify(value);
  }
  if (typeof value === "string") {
    if (hasLoneSurrogate(value)) throw new TypeError("lone surrogate is not valid JCS input");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  if (typeof value === "object") return `{${Object.keys(value).sort().map((key) => `${canonicalize(key)}:${canonicalize(value[key])}`).join(",")}}`;
  throw new TypeError(`unsupported JCS value: ${typeof value}`);
}

function base58Encode(bytes) {
  const digits = [0];
  for (const byte of bytes) {
    let carry = byte;
    for (let index = 0; index < digits.length; index += 1) {
      carry += digits[index] << 8;
      digits[index] = carry % 58;
      carry = Math.floor(carry / 58);
    }
    while (carry > 0) { digits.push(carry % 58); carry = Math.floor(carry / 58); }
  }
  let zeroes = 0;
  while (zeroes < bytes.length && bytes[zeroes] === 0) zeroes += 1;
  return "1".repeat(zeroes) + digits.reverse().map((digit) => base58Alphabet[digit]).join("");
}

function privateKeyFromSeed(seedHex) {
  return createPrivateKey({ key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), Buffer.from(seedHex, "hex")]), format: "der", type: "pkcs8" });
}

function rawPublicKeyFromSeed(seedHex) {
  return createPublicKey(privateKeyFromSeed(seedHex)).export({ format: "der", type: "spki" }).subarray(-32);
}

function multikeyFromRawEd25519(raw) {
  return `z${base58Encode(Buffer.concat([Buffer.from([0xed, 0x01]), raw]))}`;
}

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function uint32le(value) {
  const output = Buffer.alloc(4);
  output.writeUInt32LE(value >>> 0);
  return output;
}

// Fixtures use zero mtime, no optional fields, OS 255, and RFC 1951 stored
// blocks to avoid generator drift. Verifiers accept any conforming GZIP stream.
function deterministicGzip(bytes) {
  const blocks = [];
  for (let offset = 0; offset < bytes.length; offset += 65535) {
    const chunk = bytes.subarray(offset, Math.min(offset + 65535, bytes.length));
    const final = offset + chunk.length === bytes.length;
    const header = Buffer.alloc(5);
    header[0] = final ? 0x01 : 0x00;
    header.writeUInt16LE(chunk.length, 1);
    header.writeUInt16LE((~chunk.length) & 0xffff, 3);
    blocks.push(header, chunk);
  }
  return Buffer.concat([
    Buffer.from([0x1f, 0x8b, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff]),
    ...blocks,
    uint32le(crc32(bytes)),
    uint32le(bytes.length)
  ]);
}

function encodedList({ index, set }) {
  const bytes = Buffer.alloc(vector.minimumUncompressedBytes);
  // Bitstring Status List index zero is the leftmost/MSB bit.
  if (set) bytes[Math.floor(index / 8)] |= 1 << (7 - (index % 8));
  return `u${deterministicGzip(bytes).toString("base64url")}`;
}

function historyHashData(history) {
  const unsigned = structuredClone(history);
  delete unsigned.historyId;
  delete unsigned.signatures;
  return sha256(Buffer.from(canonicalize(unsigned), "utf8"));
}

function proofHashData(credential) {
  const unsecured = structuredClone(credential);
  delete unsecured.proof;
  const { proofValue, ...proofConfiguration } = credential.proof;
  return Buffer.concat([
    sha256(Buffer.from(canonicalize(proofConfiguration), "utf8")),
    sha256(Buffer.from(canonicalize(unsecured), "utf8"))
  ]);
}

function credentialHash(credential) {
  return `sha256:${sha256(Buffer.from(canonicalize(credential), "utf8")).toString("hex")}`;
}

const statusPublicKeyMultibase = multikeyFromRawEd25519(rawPublicKeyFromSeed(vector.issuerKeyMaterial.privateKeySeedHex));
if (currentHistory.keys.some((key) => key.publicKeyMultibase === statusPublicKeyMultibase)) {
  throw new Error("status-list key material must not reuse an existing issuer key");
}
const successor = structuredClone(currentHistory);
successor.sequence = currentHistory.sequence + 1;
successor.previousHistoryRef = currentHistory.historyId;
successor.publishedAt = vector.historyPublishedAt;
successor.keys = [
  ...structuredClone(currentHistory.keys),
  {
    keyId: vector.statusKey.keyId,
    verificationMethod: vector.statusKey.verificationMethod,
    publicKeyMultibase: statusPublicKeyMultibase,
    validFrom: vector.statusKey.validFrom,
    validUntil: null,
    authorizedArtifactTypes: vector.statusKey.authorizedArtifactTypes,
    authorizedProofPurposes: vector.statusKey.authorizedProofPurposes
  }
];
const successorDigest = historyHashData(successor);
successor.historyId = `sha256:${successorDigest.toString("hex")}`;
successor.signatures = {
  verificationMethod: existingTrustRoot.verificationMethod,
  historyHash: successorDigest.toString("hex"),
  signature: sign(null, successorDigest, privateKeyFromSeed(spendVector.issuerKeyMaterial.historyRootPrivateKeySeedHex)).toString("base64")
};

const trustRoot = structuredClone(existingTrustRoot);
trustRoot.highestAccepted = { sequence: successor.sequence, historyRef: successor.historyId };

const spendMethod = existingDid.verificationMethod.find((method) => method.id === currentHistory.keys[1].verificationMethod);
const statusMethod = {
  id: vector.statusKey.verificationMethod,
  type: "Multikey",
  controller: currentHistory.issuer,
  publicKeyMultibase: statusPublicKeyMultibase
};
const did = {
  id: existingDid.id,
  verificationMethod: [structuredClone(spendMethod), statusMethod],
  assertionMethod: [spendMethod.id, statusMethod.id]
};

function makeCredential({ purpose, url, index, validFrom, set }) {
  const contexts = [
    "https://www.w3.org/ns/credentials/v2",
    "https://www.w3.org/ns/credentials/status/v1",
    "https://crinkl.xyz/ns/spend/v1"
  ];
  const credential = {
    "@context": contexts,
    id: url,
    type: ["VerifiableCredential", "BitstringStatusListCredential"],
    issuer: successor.issuer,
    validFrom,
    credentialSubject: {
      id: `${url}#list`,
      type: "BitstringStatusList",
      statusPurpose: purpose,
      encodedList: encodedList({ index: Number(index), set })
    },
    proof: {
      "@context": contexts,
      type: "DataIntegrityProof",
      cryptosuite: "eddsa-jcs-2022",
      created: validFrom,
      verificationMethod: vector.statusKey.verificationMethod,
      proofPurpose: "assertionMethod",
      issuerHistoryRef: successor.historyId,
      proofValue: "z1"
    }
  };
  credential.proof.proofValue = `z${base58Encode(sign(null, proofHashData(credential), privateKeyFromSeed(vector.issuerKeyMaterial.privateKeySeedHex)))}`;
  return credential;
}

const outputs = new Map([
  ["issuer-key-history-status-current.v1.json", successor],
  ["issuer-history-trust-root.v1.json", trustRoot],
  ["did-web-vc-test.example.json", did]
]);
const statusLists = {};
for (const entry of vector.lists) {
  const clear = makeCredential({ purpose: entry.purpose, url: entry.statusListCredential, index: entry.statusListIndex, validFrom: entry.clearValidFrom, set: false });
  const set = makeCredential({ purpose: entry.purpose, url: entry.statusListCredential, index: entry.statusListIndex, validFrom: entry.setValidFrom, set: true });
  outputs.set(entry.clearFixture, clear);
  outputs.set(entry.setFixture, set);
  statusLists[entry.purpose] = {
    statusListCredential: entry.statusListCredential,
    selectedCredentialHash: credentialHash(clear),
    retainedVersions: [
      {
        credentialHash: credentialHash(clear),
        credentialFixture: entry.clearFixture
      }
    ]
  };
}
const statusResolver = {
  kind: "w3c.vc.signed-status-list-resolution.v1",
  fixtureClass: "OFFLINE_PINNED_SIGNED_BITSTRING_STATUS_LIST_RESOLVER",
  networkAccess: false,
  verificationTime: vector.verificationTime,
  freshnessPolicy: vector.freshnessPolicy,
  statusLists
};
if (credentialHash(statusResolver) !== vector.pinnedResolverSnapshotHash) throw new Error("pinned resolver snapshot hash does not match generated descriptor");
outputs.set("status-list-resolution.v1.json", statusResolver);

const write = process.argv.includes("--write");
let mismatches = 0;
for (const [name, value] of outputs) {
  const target = new URL(name, fixturesRoot);
  const expected = jsonBytes(value);
  if (write) {
    await writeFile(target, expected, "utf8");
    continue;
  }
  let actual;
  try { actual = await readFile(target, "utf8"); } catch { actual = null; }
  if (actual !== expected) {
    console.error(`generated fixture mismatch: ${name}`);
    mismatches += 1;
  }
}
if (mismatches) process.exitCode = 1;
else console.log(`w3c signed status-list generator: ${outputs.size} deterministic fixtures ${write ? "written" : "match"}`);
