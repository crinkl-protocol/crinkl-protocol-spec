#!/usr/bin/env node

import { createHash, createPrivateKey, createPublicKey, sign, verify } from "node:crypto";
import { execFileSync } from "node:child_process";
import { gunzipSync, gzipSync } from "node:zlib";
import { readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = new URL("../", import.meta.url);
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));
const schemaHelper = fileURLToPath(new URL("../conformance/w3c-vc-2.0/v1/validate_draft202012.py", import.meta.url));
const base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const MINIMUM_BYTES = 16_384;
const MAXIMUM_BYTES = 1_048_576;
const MAXIMUM_COMPRESSED_BYTES = 1_048_576;
const MAXIMUM_BASE58_ED25519_CHARACTERS = 88;
const ED25519_MULTIKEY_LENGTH = 48;
const MAXIMUM_STATUS_INDEX = MAXIMUM_BYTES * 8 - 1;
const MAXIMUM_STATUS_INDEX_TEXT = String(MAXIMUM_STATUS_INDEX);
const sha256 = (value) => createHash("sha256").update(value).digest();

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

function base58Decode(value) {
  if (typeof value !== "string" || !value.length || value.length > MAXIMUM_BASE58_ED25519_CHARACTERS) throw new TypeError("invalid base58 value");
  const bytes = [0];
  for (const character of value) {
    const digit = base58Alphabet.indexOf(character);
    if (digit < 0) throw new TypeError("invalid base58 character");
    let carry = digit;
    for (let index = 0; index < bytes.length; index += 1) {
      carry += bytes[index] * 58;
      bytes[index] = carry & 0xff;
      carry = Math.floor(carry / 256);
    }
    while (carry > 0) { bytes.push(carry & 0xff); carry = Math.floor(carry / 256); }
  }
  let zeroes = 0;
  while (zeroes < value.length && value[zeroes] === "1") zeroes += 1;
  return Buffer.concat([Buffer.alloc(zeroes), Buffer.from(bytes.reverse())]);
}

function rawEd25519FromMultikey(value) {
  if (typeof value !== "string" || value.length !== ED25519_MULTIKEY_LENGTH || !value.startsWith("z")) throw new TypeError("Multikey must use canonical Ed25519 base58-btc");
  const decoded = base58Decode(value.slice(1));
  if (decoded.length !== 34 || decoded[0] !== 0xed || decoded[1] !== 0x01) throw new TypeError("Multikey must carry Ed25519 multicodec 0xed01");
  return decoded.subarray(2);
}

function privateKeyFromSeed(seedHex) {
  return createPrivateKey({ key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), Buffer.from(seedHex, "hex")]), format: "der", type: "pkcs8" });
}

function publicKeyFromRaw(raw) {
  return createPublicKey({ key: Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), raw]), format: "der", type: "spki" });
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

export function statusResolverSnapshotHash(resolver) {
  const snapshot = structuredClone(resolver);
  for (const resolution of Object.values(snapshot.statusLists ?? {})) {
    for (const retained of resolution.retainedVersions ?? []) delete retained.credential;
  }
  return `sha256:${sha256(Buffer.from(canonicalize(snapshot), "utf8")).toString("hex")}`;
}

function historyHashData(history) {
  const unsigned = structuredClone(history);
  delete unsigned.historyId;
  delete unsigned.signatures;
  return sha256(Buffer.from(canonicalize(unsigned), "utf8"));
}

function validateDraft(target, instance) {
  try {
    execFileSync("python3", [schemaHelper, "--target", target], { input: JSON.stringify(instance), stdio: ["pipe", "ignore", "ignore"] });
    return true;
  } catch { return false; }
}

function verifyHistoryChain({ trustRoot, historyChain, selectedHistoryRef }) {
  if (!trustRoot || trustRoot.fixtureClass !== "OUT_OF_BAND_PINNED_ISSUER_HISTORY_TRUST_ROOT" || !Array.isArray(historyChain)) return { code: "issuer_history_unavailable" };
  const byRef = new Map();
  const bySequence = new Map();
  for (const history of historyChain) {
    if (!validateDraft("history", history)) return { code: "issuer_history_invalid" };
    if (history.issuer !== trustRoot.issuer) return { code: "issuer_history_invalid" };
    const keyIds = new Set();
    const methods = new Set();
    const publicKeys = new Set();
    for (const key of history.keys) {
      const validFrom = Date.parse(key.validFrom);
      const validUntil = key.validUntil === null ? Number.POSITIVE_INFINITY : Date.parse(key.validUntil);
      if (keyIds.has(key.keyId) || methods.has(key.verificationMethod) || publicKeys.has(key.publicKeyMultibase) || key.verificationMethod !== `${history.issuer}#${key.keyId}` || !Number.isFinite(validFrom) || (key.validUntil !== null && !Number.isFinite(validUntil)) || validUntil <= validFrom) return { code: "issuer_history_invalid" };
      keyIds.add(key.keyId);
      methods.add(key.verificationMethod);
      publicKeys.add(key.publicKeyMultibase);
    }
    const digest = historyHashData(history);
    if (history.historyId !== `sha256:${digest.toString("hex")}` || history.signatures.historyHash !== digest.toString("hex") || history.signatures.verificationMethod !== trustRoot.verificationMethod) return { code: "issuer_history_invalid" };
    try {
      const signature = Buffer.from(history.signatures.signature, "base64");
      if (signature.length !== 64 || signature.toString("base64") !== history.signatures.signature || !verify(null, digest, publicKeyFromRaw(rawEd25519FromMultikey(trustRoot.publicKeyMultibase)), signature)) return { code: "issuer_history_invalid" };
    } catch { return { code: "issuer_history_invalid" }; }
    if (byRef.has(history.historyId) || bySequence.has(history.sequence)) return { code: "issuer_history_invalid" };
    byRef.set(history.historyId, history);
    bySequence.set(history.sequence, history.historyId);
  }
  const selected = byRef.get(selectedHistoryRef);
  const bootstrap = byRef.get(trustRoot.pinnedHistoryRef);
  if (!selected || !bootstrap) return { code: "issuer_history_mismatch" };
  if (!Number.isSafeInteger(trustRoot.minimumSequence) || bootstrap.sequence !== trustRoot.minimumSequence || bootstrap.previousHistoryRef !== null) return { code: "issuer_history_invalid" };
  if (selected.sequence < trustRoot.highestAccepted.sequence || (selected.sequence === trustRoot.highestAccepted.sequence && selected.historyId !== trustRoot.highestAccepted.historyRef)) return { code: "issuer_history_rollback" };
  if (selected.sequence !== trustRoot.highestAccepted.sequence || selected.historyId !== trustRoot.highestAccepted.historyRef) return { code: "issuer_history_mismatch" };
  const selectedChainRefs = new Set([selected.historyId]);
  let cursor = selected;
  while (cursor.sequence > bootstrap.sequence) {
    const previous = byRef.get(cursor.previousHistoryRef);
    if (!previous || cursor.sequence !== previous.sequence + 1 || Date.parse(cursor.publishedAt) <= Date.parse(previous.publishedAt) || cursor.refreshServiceBaseUrl !== previous.refreshServiceBaseUrl) return { code: "issuer_history_invalid" };
    const nextKeys = new Map(cursor.keys.map((key) => [key.keyId, key]));
    for (const prior of previous.keys) {
      const next = nextKeys.get(prior.keyId);
      if (!next) return { code: "issuer_history_invalid" };
      const validUntilTightens = prior.validUntil === null || (next.validUntil !== null && Date.parse(next.validUntil) <= Date.parse(prior.validUntil));
      if (next.verificationMethod !== prior.verificationMethod || next.publicKeyMultibase !== prior.publicKeyMultibase || next.validFrom !== prior.validFrom || JSON.stringify(next.authorizedArtifactTypes) !== JSON.stringify(prior.authorizedArtifactTypes) || JSON.stringify(next.authorizedProofPurposes) !== JSON.stringify(prior.authorizedProofPurposes) || !validUntilTightens) return { code: "issuer_history_invalid" };
    }
    selectedChainRefs.add(previous.historyId);
    cursor = previous;
  }
  if (cursor.historyId !== bootstrap.historyId || selectedChainRefs.size !== byRef.size) return { code: "issuer_history_invalid" };
  return { code: "accepted", selected, byRef, selectedChainRefs };
}

function decodeEncodedList(value) {
  const maximumEncodedLength = 1 + Math.ceil(MAXIMUM_COMPRESSED_BYTES * 4 / 3);
  if (typeof value !== "string" || value.length > maximumEncodedLength || !/^u[A-Za-z0-9_-]+$/.test(value)) return { code: "status_list_encoding_invalid" };
  let gzip;
  try {
    gzip = Buffer.from(value.slice(1), "base64url");
    if (`u${gzip.toString("base64url")}` !== value || gzip.length > MAXIMUM_COMPRESSED_BYTES || gzip.length < 18 || gzip[0] !== 0x1f || gzip[1] !== 0x8b || gzip[2] !== 0x08) return { code: "status_list_encoding_invalid" };
  } catch { return { code: "status_list_encoding_invalid" }; }
  let bytes;
  try { bytes = gunzipSync(gzip, { maxOutputLength: MAXIMUM_BYTES }); } catch { return { code: "status_list_gzip_invalid" }; }
  if (bytes.length < MINIMUM_BYTES) return { code: "status_list_too_short" };
  return { code: "accepted", bytes };
}

function verifyRetainedCredential({ credential, purpose, resolution, resolver, chain }) {
  if (!validateDraft("statusCredential", credential)) return { code: "status_list_schema_invalid" };
  if (credential.id !== resolution.statusListCredential || credential.credentialSubject.id !== `${credential.id}#list` || credential.credentialSubject.statusPurpose !== purpose || credential.issuer !== chain.selected.issuer) return { code: "status_list_binding_invalid" };
  if (JSON.stringify(credential.proof["@context"]) !== JSON.stringify(credential["@context"]) || credential.proof.type !== "DataIntegrityProof" || credential.proof.cryptosuite !== "eddsa-jcs-2022" || credential.proof.proofPurpose !== "assertionMethod") return { code: "status_proof_configuration_invalid" };
  const issuanceHistory = chain.byRef.get(credential.proof.issuerHistoryRef);
  if (!issuanceHistory || !chain.selectedChainRefs.has(issuanceHistory.historyId)) return { code: "issuer_history_mismatch" };
  const key = issuanceHistory.keys.find((candidate) => candidate.verificationMethod === credential.proof.verificationMethod);
  const retainedKey = chain.selected.keys.find((candidate) => candidate.verificationMethod === credential.proof.verificationMethod);
  if (!key || !retainedKey) return { code: "status_key_unauthorized" };
  if (key.keyId !== retainedKey.keyId || key.publicKeyMultibase !== retainedKey.publicKeyMultibase || key.validFrom !== retainedKey.validFrom || JSON.stringify(key.authorizedArtifactTypes) !== JSON.stringify(retainedKey.authorizedArtifactTypes) || JSON.stringify(key.authorizedProofPurposes) !== JSON.stringify(retainedKey.authorizedProofPurposes)) return { code: "status_key_continuity_invalid" };
  if (!key.authorizedArtifactTypes.includes("BITSTRING_STATUS_LIST_CREDENTIAL") || !key.authorizedProofPurposes.includes("assertionMethod")) return { code: "status_key_unauthorized" };
  const proofCreated = Date.parse(credential.proof.created);
  const validFrom = Date.parse(credential.validFrom);
  const keyFrom = Date.parse(key.validFrom);
  const keyUntil = key.validUntil === null ? Number.POSITIVE_INFINITY : Date.parse(key.validUntil);
  const retainedUntil = retainedKey.validUntil === null ? Number.POSITIVE_INFINITY : Date.parse(retainedKey.validUntil);
  const verificationTime = Date.parse(resolver.verificationTime);
  if (![proofCreated, validFrom, keyFrom, verificationTime].every(Number.isFinite) || (key.validUntil !== null && !Number.isFinite(keyUntil)) || (retainedKey.validUntil !== null && !Number.isFinite(retainedUntil)) || proofCreated < validFrom || proofCreated > verificationTime || proofCreated < keyFrom || proofCreated >= keyUntil || proofCreated >= retainedUntil || proofCreated < Date.parse(issuanceHistory.publishedAt)) return { code: "status_time_invalid" };
  if (verificationTime < validFrom) return { code: "status_time_invalid" };
  try {
    if (!credential.proof.proofValue.startsWith("z")) return { code: "status_proof_invalid" };
    const signature = base58Decode(credential.proof.proofValue.slice(1));
    if (signature.length !== 64 || `z${base58Encode(signature)}` !== credential.proof.proofValue || !verify(null, proofHashData(credential), publicKeyFromRaw(rawEd25519FromMultikey(key.publicKeyMultibase)), signature)) return { code: "status_proof_invalid" };
  } catch { return { code: "status_proof_invalid" }; }
  const decoded = decodeEncodedList(credential.credentialSubject.encodedList);
  if (decoded.code !== "accepted") return decoded;
  return { code: "accepted", credential, bytes: decoded.bytes, validFrom };
}

export function verifySignedStatusEntry({ entry, purpose, resolver, pinnedResolverSnapshotHash, trustRoot, historyChain, selectedHistoryRef }) {
  const maximumAgeSeconds = resolver?.freshnessPolicy?.maximumAgeSeconds;
  if (resolver?.fixtureClass !== "OFFLINE_PINNED_SIGNED_BITSTRING_STATUS_LIST_RESOLVER" || resolver.networkAccess !== false || resolver.freshnessPolicy?.networkAccess !== false || resolver.freshnessPolicy?.requireRetainedCredential !== true || !Number.isSafeInteger(maximumAgeSeconds) || maximumAgeSeconds <= 0) return "status_list_resolver_invalid";
  if (!/^sha256:[0-9a-f]{64}$/.test(pinnedResolverSnapshotHash) || statusResolverSnapshotHash(resolver) !== pinnedResolverSnapshotHash) return "status_resolver_snapshot_invalid";
  const resolution = resolver.statusLists?.[purpose];
  if (!resolution || !Array.isArray(resolution.retainedVersions) || resolution.retainedVersions.length === 0 || typeof resolution.selectedCredentialHash !== "string") return "status_list_unavailable";
  if (entry.type !== "BitstringStatusListEntry" || entry.statusPurpose !== purpose || entry.statusListCredential !== resolution.statusListCredential || typeof entry.statusListIndex !== "string" || entry.id !== `${entry.statusListCredential}#${entry.statusListIndex}`) return "status_entry_mismatch";
  if (entry.statusListIndex.length > MAXIMUM_STATUS_INDEX_TEXT.length) return "status_index_out_of_range";
  if (!/^(0|[1-9][0-9]*)$/.test(entry.statusListIndex)) return "status_entry_mismatch";
  if (entry.statusListIndex.length === MAXIMUM_STATUS_INDEX_TEXT.length && entry.statusListIndex > MAXIMUM_STATUS_INDEX_TEXT) return "status_index_out_of_range";
  const chain = verifyHistoryChain({ trustRoot, historyChain, selectedHistoryRef });
  if (chain.code !== "accepted") return chain.code;
  const authenticated = new Map();
  for (const retained of resolution.retainedVersions) {
    if (!retained?.credential || !/^sha256:[0-9a-f]{64}$/.test(retained.credentialHash) || retained.credentialHash !== credentialHash(retained.credential) || authenticated.has(retained.credentialHash)) return "status_retention_invalid";
    const result = verifyRetainedCredential({ credential: retained.credential, purpose, resolution, resolver, chain });
    if (result.code !== "accepted") return result.code;
    authenticated.set(retained.credentialHash, result);
  }
  const selected = authenticated.get(resolution.selectedCredentialHash);
  if (!selected) return "status_list_unavailable";
  const highestTime = Math.max(...[...authenticated.values()].map((candidate) => candidate.validFrom));
  const highest = [...authenticated.entries()].filter(([, candidate]) => candidate.validFrom === highestTime);
  if (highest.length !== 1) return "status_retention_invalid";
  if (highest[0][0] !== resolution.selectedCredentialHash) return "status_list_rollback";
  const ordered = [...authenticated.values()].sort((left, right) => left.validFrom - right.validFrom);
  for (let version = 1; version < ordered.length; version += 1) {
    const older = ordered[version - 1].bytes;
    const newer = ordered[version].bytes;
    if (newer.length < older.length) return "status_list_non_monotonic";
    for (let offset = 0; offset < older.length; offset += 1) {
      if ((older[offset] & ~(newer[offset] ?? 0)) !== 0) return "status_list_non_monotonic";
    }
  }
  const verificationTime = Date.parse(resolver.verificationTime);
  if (verificationTime - selected.validFrom > resolver.freshnessPolicy.maximumAgeSeconds * 1000) return "status_list_stale";
  const numericIndex = Number(entry.statusListIndex);
  if (numericIndex >= selected.bytes.length * 8) return "status_index_out_of_range";
  const set = (selected.bytes[Math.floor(numericIndex / 8)] & (1 << (7 - (numericIndex % 8)))) !== 0;
  if (!set) return "accepted";
  return purpose === "revocation" ? "revoked" : "refresh_required";
}

function resign(credential, seedHex) {
  credential.proof.proofValue = `z${base58Encode(sign(null, proofHashData(credential), privateKeyFromSeed(seedHex)))}`;
}

function resignHistory(history, seedHex, verificationMethod) {
  delete history.historyId;
  delete history.signatures;
  const digest = historyHashData(history);
  history.historyId = `sha256:${digest.toString("hex")}`;
  history.signatures = {
    verificationMethod,
    historyHash: digest.toString("hex"),
    signature: sign(null, digest, privateKeyFromSeed(seedHex)).toString("base64")
  };
}

async function main() {
  const vector = await readJson("conformance/w3c-vc-2.0/v1/vectors/bitstring-status-list-credential.v1.json");
  const manifest = await readJson("conformance/w3c-vc-2.0/v1/manifest.json");
  const spendVector = await readJson("conformance/w3c-vc-2.0/v1/vectors/spend-attestation-credential.v1.json");
  const trustRoot = await readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-history-trust-root.v1.json");
  const histories = await Promise.all([
    readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-bootstrap.v1.json"),
    readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-current.v1.json"),
    readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-status-current.v1.json")
  ]);
  const resolverConfig = await readJson("conformance/w3c-vc-2.0/v1/fixtures/status-list-resolution.v1.json");
  const fixtures = new Map();
  for (const list of vector.lists) {
    fixtures.set(list.clearFixture, await readJson(`conformance/w3c-vc-2.0/v1/fixtures/${list.clearFixture}`));
    fixtures.set(list.setFixture, await readJson(`conformance/w3c-vc-2.0/v1/fixtures/${list.setFixture}`));
  }
  const resolverFor = (purpose, fixture) => {
    const resolver = structuredClone(resolverConfig);
    const credential = structuredClone(fixtures.get(fixture));
    const hash = credentialHash(credential);
    resolver.statusLists[purpose].selectedCredentialHash = hash;
    resolver.statusLists[purpose].retainedVersions = [{ credentialHash: hash, credentialFixture: fixture, credential }];
    return resolver;
  };
  const rehashSelected = (resolver, purpose) => {
    const resolution = resolver.statusLists[purpose];
    const selected = resolution.retainedVersions.find((retained) => retained.credentialHash === resolution.selectedCredentialHash) ?? resolution.retainedVersions[0];
    selected.credentialHash = credentialHash(selected.credential);
    resolution.selectedCredentialHash = selected.credentialHash;
  };
  const entryFor = (list) => ({ id: `${list.statusListCredential}#${list.statusListIndex}`, type: "BitstringStatusListEntry", statusPurpose: list.purpose, statusListIndex: list.statusListIndex, statusListCredential: list.statusListCredential });
  if (vector.pinnedResolverSnapshotHash !== statusResolverSnapshotHash(resolverConfig) || manifest.statusResolverSnapshotSha256 !== vector.pinnedResolverSnapshotHash) throw new Error("pinned resolver snapshot hash mismatch");
  let positives = 0;
  for (const list of vector.lists) {
    const entry = entryFor(list);
    const clearResolver = resolverFor(list.purpose, list.clearFixture);
    const setResolver = resolverFor(list.purpose, list.setFixture);
    const clearSnapshotHash = vector.pinnedResolverSnapshotHash;
    const setSnapshotHash = vector.alternativePinnedResolverSnapshotHashes[`${list.purpose}Set`];
    if (statusResolverSnapshotHash(clearResolver) !== clearSnapshotHash || statusResolverSnapshotHash(setResolver) !== setSnapshotHash) throw new Error(`${list.purpose} resolver snapshot pin mismatch`);
    const clear = verifySignedStatusEntry({ entry, purpose: list.purpose, resolver: clearResolver, pinnedResolverSnapshotHash: clearSnapshotHash, trustRoot, historyChain: histories, selectedHistoryRef: histories[2].historyId });
    const set = verifySignedStatusEntry({ entry, purpose: list.purpose, resolver: setResolver, pinnedResolverSnapshotHash: setSnapshotHash, trustRoot, historyChain: histories, selectedHistoryRef: histories[2].historyId });
    if (clear !== "accepted" || set !== (list.purpose === "revocation" ? "revoked" : "refresh_required")) throw new Error(`${list.purpose} positive results mismatch: ${clear}/${set}`);
    positives += 2;
  }
  const revocation = vector.lists[0];
  const baseEntry = entryFor(revocation);
  const baseResolver = resolverFor("revocation", revocation.clearFixture);
  const cases = [];
  if (statusResolverSnapshotHash(baseResolver) !== vector.pinnedResolverSnapshotHash) throw new Error("base adversarial resolver snapshot pin mismatch");
  // Most cases intentionally model a caller pinning the mutated descriptor so
  // they can reach a deeper proof/history/codec invariant. Pin-integrity cases
  // preserve the original declared hash instead.
  const add = (id, mutate, expected, { preserveSnapshotPin = false } = {}) => { const context = { entry: structuredClone(baseEntry), resolver: structuredClone(baseResolver), pinnedResolverSnapshotHash: vector.pinnedResolverSnapshotHash, trustRoot: structuredClone(trustRoot), histories: structuredClone(histories) }; mutate(context); if (!preserveSnapshotPin) context.pinnedResolverSnapshotHash = statusResolverSnapshotHash(context.resolver); cases.push({ id, context, expected }); };
  const selectedCredential = (resolver) => resolver.statusLists.revocation.retainedVersions[0].credential;
  const resignAndRehash = (resolver) => { resign(selectedCredential(resolver), vector.issuerKeyMaterial.privateKeySeedHex); rehashSelected(resolver, "revocation"); };
  const resignSelectedStatusHistory = (context) => {
    const history = context.histories[2];
    resignHistory(history, spendVector.issuerKeyMaterial.historyRootPrivateKeySeedHex, context.trustRoot.verificationMethod);
    context.trustRoot.highestAccepted = { sequence: history.sequence, historyRef: history.historyId };
    const credential = selectedCredential(context.resolver);
    credential.proof.issuerHistoryRef = history.historyId;
    resignAndRehash(context.resolver);
  };
  const mutateStatusHistory = (context, mutate) => {
    mutate(context.histories[2].keys.find((key) => key.verificationMethod === vector.statusKey.verificationMethod));
    resignSelectedStatusHistory(context);
  };
  add("tampered-proof", ({ resolver }) => { const credential = selectedCredential(resolver); credential.proof.proofValue = `z1${credential.proof.proofValue.slice(2)}`; rehashSelected(resolver, "revocation"); }, "status_proof_invalid");
  add("tampered-encoded-bytes", ({ resolver }) => { const credential = selectedCredential(resolver); const original = credential.credentialSubject.encodedList; const replacement = original[1] === "A" ? "B" : "A"; credential.credentialSubject.encodedList = `u${replacement}${original.slice(2)}`; if (credential.credentialSubject.encodedList === original) throw new Error("encoded-list tamper did not change bytes"); rehashSelected(resolver, "revocation"); }, "status_proof_invalid");
  add("wrong-purpose", ({ entry }) => { entry.statusPurpose = "refresh"; }, "status_entry_mismatch");
  add("wrong-url", ({ entry }) => { entry.statusListCredential = "https://vc-test.example/status/revocation/missing"; entry.id = `${entry.statusListCredential}#7`; }, "status_entry_mismatch");
  add("out-of-range-index", ({ entry }) => { entry.statusListIndex = String(MAXIMUM_BYTES * 8); entry.id = `${entry.statusListCredential}#${entry.statusListIndex}`; }, "status_index_out_of_range");
  add("noncanonical-base64url", ({ resolver }) => { selectedCredential(resolver).credentialSubject.encodedList += "="; resignAndRehash(resolver); }, "status_list_schema_invalid");
  add("short-list", ({ resolver }) => { selectedCredential(resolver).credentialSubject.encodedList = `u${gzipSync(Buffer.alloc(8), { mtime: 0 }).toString("base64url")}`; resignAndRehash(resolver); }, "status_list_too_short");
  add("malformed-gzip", ({ resolver }) => { const malformed = Buffer.concat([Buffer.from([0x1f, 0x8b, 0x08, 0, 0, 0, 0, 0, 0, 0xff]), Buffer.alloc(12, 0xff)]); selectedCredential(resolver).credentialSubject.encodedList = `u${malformed.toString("base64url")}`; resignAndRehash(resolver); }, "status_list_gzip_invalid");
  add("unavailable-resolver", ({ resolver }) => { delete resolver.statusLists.revocation.retainedVersions; }, "status_list_unavailable");
  add("unavailable-history", (context) => { context.histories = null; }, "issuer_history_unavailable");
  add("retained-history-rollback", ({ histories }) => { histories.pop(); }, "issuer_history_rollback");
  add("stale-retained-status", ({ resolver }) => { resolver.verificationTime = "2026-08-07T16:00:00.000Z"; }, "status_list_stale");
  add("proof-created-after-verification", ({ resolver }) => { selectedCredential(resolver).proof.created = "2026-08-07T14:11:00.000Z"; resignAndRehash(resolver); }, "status_time_invalid");
  add("status-key-artifact-scope", (context) => { mutateStatusHistory(context, (key) => { key.authorizedArtifactTypes = ["SPEND_ATTESTATION_CREDENTIAL"]; }); }, "status_key_unauthorized");
  add("status-key-proof-purpose", (context) => { mutateStatusHistory(context, (key) => { key.authorizedProofPurposes = ["authentication"]; }); }, "status_key_unauthorized");
  add("status-key-expired-at-issuance", (context) => { mutateStatusHistory(context, (key) => { key.validUntil = "2026-08-07T14:00:30.000Z"; }); }, "status_time_invalid");
  add("oversized-status-multikey", (context) => { mutateStatusHistory(context, (key) => { key.publicKeyMultibase = `z${"1".repeat(4096)}`; }); }, "status_proof_invalid");
  add("trust-root-minimum-sequence-mismatch", ({ trustRoot }) => { trustRoot.minimumSequence = 999; }, "issuer_history_invalid");
  add("non-genesis-bootstrap", ({ histories, trustRoot }) => { histories.shift(); trustRoot.pinnedHistoryRef = histories[0].historyId; trustRoot.minimumSequence = histories[0].sequence; }, "issuer_history_invalid");
  add("changed-refresh-service-base", (context) => { context.histories[2].refreshServiceBaseUrl = "https://changed.example"; resignSelectedStatusHistory(context); }, "issuer_history_invalid");
  add("history-missing-prior-key", ({ histories, trustRoot }) => { const history = histories[2]; history.keys.shift(); resignHistory(history, spendVector.issuerKeyMaterial.historyRootPrivateKeySeedHex, trustRoot.verificationMethod); trustRoot.highestAccepted = { sequence: history.sequence, historyRef: history.historyId }; }, "issuer_history_invalid");
  add("retained-content-hash-mismatch", ({ resolver }) => { resolver.statusLists.revocation.retainedVersions[0].credentialHash = `sha256:${"0".repeat(64)}`; }, "status_retention_invalid");
  add("retained-status-rollback", ({ resolver }) => {
    const setCredential = structuredClone(fixtures.get(revocation.setFixture));
    resolver.statusLists.revocation.retainedVersions.push({ credentialHash: credentialHash(setCredential), credentialFixture: revocation.setFixture, credential: setCredential });
  }, "status_list_rollback");
  add("omitted-newer-version-against-pinned-snapshot", (context) => {
    const { resolver } = context;
    const setCredential = structuredClone(fixtures.get(revocation.setFixture));
    resolver.statusLists.revocation.retainedVersions.push({ credentialHash: credentialHash(setCredential), credentialFixture: revocation.setFixture, credential: setCredential });
    resolver.statusLists.revocation.selectedCredentialHash = credentialHash(setCredential);
    context.pinnedResolverSnapshotHash = statusResolverSnapshotHash(resolver);
    resolver.statusLists.revocation.retainedVersions.pop();
    resolver.statusLists.revocation.selectedCredentialHash = resolver.statusLists.revocation.retainedVersions[0].credentialHash;
  }, "status_resolver_snapshot_invalid", { preserveSnapshotPin: true });
  add("signed-set-then-clear-refused", ({ resolver }) => {
    const setCredential = structuredClone(fixtures.get(revocation.setFixture));
    const newerClear = structuredClone(fixtures.get(revocation.clearFixture));
    newerClear.validFrom = "2026-08-07T14:03:00.000Z";
    newerClear.proof.created = newerClear.validFrom;
    resign(newerClear, vector.issuerKeyMaterial.privateKeySeedHex);
    const setHash = credentialHash(setCredential);
    const clearHash = credentialHash(newerClear);
    resolver.statusLists.revocation.retainedVersions = [
      { credentialHash: setHash, credentialFixture: revocation.setFixture, credential: setCredential },
      { credentialHash: clearHash, credentialFixture: "generated-newer-clear", credential: newerClear }
    ];
    resolver.statusLists.revocation.selectedCredentialHash = clearHash;
  }, "status_list_non_monotonic");
  add("signed-newer-shorter-list-refused", ({ resolver }) => {
    const olderLong = structuredClone(fixtures.get(revocation.clearFixture));
    olderLong.credentialSubject.encodedList = `u${gzipSync(Buffer.alloc(MINIMUM_BYTES + 1), { level: 9, mtime: 0 }).toString("base64url")}`;
    resign(olderLong, vector.issuerKeyMaterial.privateKeySeedHex);
    const newerShort = structuredClone(fixtures.get(revocation.clearFixture));
    newerShort.validFrom = "2026-08-07T14:03:00.000Z";
    newerShort.proof.created = newerShort.validFrom;
    resign(newerShort, vector.issuerKeyMaterial.privateKeySeedHex);
    const olderHash = credentialHash(olderLong);
    const newerHash = credentialHash(newerShort);
    resolver.statusLists.revocation.retainedVersions = [
      { credentialHash: olderHash, credentialFixture: "generated-older-long", credential: olderLong },
      { credentialHash: newerHash, credentialFixture: "generated-newer-short", credential: newerShort }
    ];
    resolver.statusLists.revocation.selectedCredentialHash = newerHash;
  }, "status_list_non_monotonic");
  add("stale-predecessor-fresh-selected", ({ resolver }) => {
    const olderClear = structuredClone(fixtures.get(revocation.clearFixture));
    const freshSet = structuredClone(fixtures.get(revocation.setFixture));
    freshSet.validFrom = "2026-08-07T15:01:00.000Z";
    freshSet.proof.created = freshSet.validFrom;
    resign(freshSet, vector.issuerKeyMaterial.privateKeySeedHex);
    const olderHash = credentialHash(olderClear);
    const freshHash = credentialHash(freshSet);
    resolver.verificationTime = "2026-08-07T15:02:00.000Z";
    resolver.statusLists.revocation.retainedVersions = [
      { credentialHash: olderHash, credentialFixture: revocation.clearFixture, credential: olderClear },
      { credentialHash: freshHash, credentialFixture: "generated-fresh-set", credential: freshSet }
    ];
    resolver.statusLists.revocation.selectedCredentialHash = freshHash;
  }, "revoked");
  add("msb-vs-lsb-discriminator", ({ resolver, entry }) => {
    const credential = selectedCredential(resolver);
    const bytes = Buffer.alloc(MINIMUM_BYTES);
    bytes[0] = 0x80;
    credential.credentialSubject.encodedList = `u${gzipSync(bytes, { level: 9, mtime: 0 }).toString("base64url")}`;
    resignAndRehash(resolver);
    entry.statusListIndex = "7";
    entry.id = `${entry.statusListCredential}#7`;
  }, "accepted");
  for (const { id, context, expected } of cases) {
    const actual = verifySignedStatusEntry({ entry: context.entry, purpose: "revocation", resolver: context.resolver, pinnedResolverSnapshotHash: context.pinnedResolverSnapshotHash, trustRoot: context.trustRoot, historyChain: context.histories, selectedHistoryRef: context.histories?.at(-1)?.historyId });
    if (actual !== expected) throw new Error(`${id} expected ${expected}, received ${actual}`);
  }
  if (decodeEncodedList("uAA==").code !== "status_list_encoding_invalid") throw new Error("runtime decoder accepted padded base64url");
  if (decodeEncodedList(`u${"A".repeat(1 + Math.ceil(MAXIMUM_COMPRESSED_BYTES * 4 / 3))}`).code !== "status_list_encoding_invalid") throw new Error("runtime decoder accepted oversized compressed input");
  const diagnosticOutcomes = cases.filter(({ expected }) => ["accepted", "revoked", "refresh_required"].includes(expected)).length;
  const negativeRejects = cases.length - diagnosticOutcomes;
  if (vector.adversarialCaseCount !== cases.length || vector.negativeRejectCaseCount !== negativeRejects || vector.diagnosticOutcomeCaseCount !== diagnosticOutcomes) throw new Error("declared status-list case counts do not match executable cases");
  console.log(`w3c signed bitstring status-list: ${positives} positive clear/set decisions, ${negativeRejects} negative rejects, ${diagnosticOutcomes} diagnostic outcomes`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();
