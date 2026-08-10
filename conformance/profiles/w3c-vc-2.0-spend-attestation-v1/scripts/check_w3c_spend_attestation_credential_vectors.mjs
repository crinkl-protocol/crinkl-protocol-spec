#!/usr/bin/env node

// CONFORMANCE_FIXTURE_HARNESS_NOT_GENERIC_VERIFIER
import { createHash, createPrivateKey, createPublicKey, sign, verify } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { statusResolverSnapshotHash, verifySignedStatusEntry } from "./check_w3c_bitstring_status_list_vectors.mjs";

const root = new URL("../", import.meta.url);
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));
const [vector, statusVector, contextFile, did, trustRoot, bootstrapHistory, currentHistory, statusHistory, status, revocationClear, revocationSet, refreshClear, refreshSet, nativeVector] = await Promise.all([
  readJson("conformance/w3c-vc-2.0/v1/vectors/spend-attestation-credential.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/vectors/bitstring-status-list-credential.v1.json"),
  readJson("protocol/context/spend-v1.jsonld"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/did-web-vc-test.example.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-history-trust-root.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-bootstrap.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-current.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/issuer-key-history-status-current.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/status-list-resolution.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-revocation-clear.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-revocation-set.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-refresh-clear.v1.json"),
  readJson("conformance/w3c-vc-2.0/v1/fixtures/bitstring-status-list-refresh-set.v1.json"),
  readJson("conformance/spend-attestation-portability/v1/vectors/spend-attestation.wallet-omitted.v1.json")
]);

const assert = (condition, message) => { if (!condition) throw new Error(message); };
const sha256 = (value) => createHash("sha256").update(value).digest();
const base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const MAXIMUM_BASE58_ED25519_CHARACTERS = 88;
const ED25519_MULTIKEY_LENGTH = 48;
const schemaHelper = fileURLToPath(new URL("../conformance/w3c-vc-2.0/v1/validate_draft202012.py", import.meta.url));
const unreserved = /^[A-Za-z0-9._~-]$/;

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

function credentialHash(value) {
  return `sha256:${sha256(Buffer.from(canonicalize(value), "utf8")).toString("hex")}`;
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
  assert(typeof value === "string" && value.length > 0 && value.length <= MAXIMUM_BASE58_ED25519_CHARACTERS, "invalid base58 value");
  const bytes = [0];
  for (const character of value) {
    const digit = base58Alphabet.indexOf(character);
    assert(digit >= 0, "invalid base58 character");
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

function multikeyFromRawEd25519(raw) {
  assert(raw.length === 32, "Ed25519 public key must be 32 bytes");
  return `z${base58Encode(Buffer.concat([Buffer.from([0xed, 0x01]), raw]))}`;
}

function rawEd25519FromMultikey(value) {
  assert(typeof value === "string" && value.length === ED25519_MULTIKEY_LENGTH && value.startsWith("z"), "Multikey must use canonical Ed25519 base58-btc");
  const decoded = base58Decode(value.slice(1));
  assert(decoded.length === 34 && decoded[0] === 0xed && decoded[1] === 0x01, "Multikey must carry Ed25519 multicodec 0xed01");
  assert(multikeyFromRawEd25519(decoded.subarray(2)) === value, "Multikey must be canonical");
  return decoded.subarray(2);
}

function privateKeyFromSeed(seedHex) {
  return createPrivateKey({ key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), Buffer.from(seedHex, "hex")]), format: "der", type: "pkcs8" });
}

function rawPublicKeyFromSeed(seedHex) {
  return createPublicKey(privateKeyFromSeed(seedHex)).export({ format: "der", type: "spki" }).subarray(-32);
}

function publicKeyFromRaw(raw) {
  return createPublicKey({ key: Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), raw]), format: "der", type: "spki" });
}

function percentEncodeComponent(value) {
  let encoded = "";
  for (const byte of Buffer.from(value, "utf8")) {
    const character = String.fromCharCode(byte);
    encoded += unreserved.test(character) ? character : `%${byte.toString(16).toUpperCase().padStart(2, "0")}`;
  }
  return encoded;
}

function subjectId(subject) {
  return `urn:crinkl:spend:${percentEncodeComponent(subject.spendStreamNamespaceRef)}:${percentEncodeComponent(subject.issuerId)}:${percentEncodeComponent(subject.spendId)}`;
}

function refreshUrl(subject, history) {
  return `${history.refreshServiceBaseUrl}/tokens/${percentEncodeComponent(subject.spendStreamNamespaceRef)}/${percentEncodeComponent(subject.issuerId)}/${percentEncodeComponent(subject.spendId)}/head`;
}

function proofHashData(credential) {
  const unsecured = structuredClone(credential);
  delete unsecured.proof;
  const { proofValue, ...proofConfiguration } = credential.proof;
  return Buffer.concat([sha256(Buffer.from(canonicalize(proofConfiguration), "utf8")), sha256(Buffer.from(canonicalize(unsecured), "utf8"))]);
}

function historyHashData(history) {
  const unsigned = structuredClone(history);
  delete unsigned.historyId;
  delete unsigned.signatures;
  return sha256(Buffer.from(canonicalize(unsigned), "utf8"));
}

function signHistory(history, privateKeySeedHex, verificationMethod) {
  const digest = historyHashData(history);
  history.historyId = `sha256:${digest.toString("hex")}`;
  history.signatures = {
    verificationMethod,
    historyHash: digest.toString("hex"),
    signature: sign(null, digest, privateKeyFromSeed(privateKeySeedHex)).toString("base64")
  };
  return history;
}

function validateDraft(target, instance) {
  try {
    execFileSync("python3", [schemaHelper, "--target", target], {
      input: JSON.stringify(instance),
      stdio: ["pipe", "ignore", "ignore"]
    });
    return true;
  } catch { return false; }
}

function applyMutation(object, mutation, values = {}) {
  const parts = mutation.path.slice(1).split("/").map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"));
  const key = parts.pop();
  let target = object;
  for (const part of parts) target = Array.isArray(target) ? target[Number(part)] : target[part];
  if (mutation.op === "remove") {
    if (Array.isArray(target)) target.splice(Number(key), 1);
    else delete target[key];
  } else if (mutation.op === "add" || mutation.op === "replace") {
    target[Array.isArray(target) ? Number(key) : key] = Object.hasOwn(mutation, "valueFrom") ? values[mutation.valueFrom] : mutation.value;
  } else throw new Error(`unsupported mutation operation ${mutation.op}`);
}

function exactKeys(value, keys) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function validUntilTightens(previous, next) {
  if (previous === null) return true;
  return next !== null && Date.parse(next) <= Date.parse(previous);
}

function verifyHistory(history, rootTrust) {
  if (!validateDraft("history", history)) return "issuer_history_schema_invalid";
  if (history.issuer !== rootTrust.issuer || history.signatures.verificationMethod !== rootTrust.verificationMethod) return "issuer_history_root_key_mismatch";
  if (!Number.isFinite(Date.parse(history.publishedAt))) return "issuer_history_time_invalid";
  const keyIds = new Set();
  const methods = new Set();
  const publicKeys = new Set();
  for (const key of history.keys) {
    if (keyIds.has(key.keyId) || methods.has(key.verificationMethod) || publicKeys.has(key.publicKeyMultibase) || key.verificationMethod !== `${history.issuer}#${key.keyId}`) return "issuer_history_key_ambiguity";
    const validFrom = Date.parse(key.validFrom);
    const validUntil = key.validUntil === null ? Number.POSITIVE_INFINITY : Date.parse(key.validUntil);
    if (!Number.isFinite(validFrom) || (key.validUntil !== null && !Number.isFinite(validUntil)) || validUntil <= validFrom) return "issuer_history_time_invalid";
    keyIds.add(key.keyId);
    methods.add(key.verificationMethod);
    publicKeys.add(key.publicKeyMultibase);
  }
  let digest;
  try { digest = historyHashData(history); } catch { return "issuer_history_hash_invalid"; }
  if (history.historyId !== `sha256:${digest.toString("hex")}` || history.signatures.historyHash !== digest.toString("hex")) return "issuer_history_hash_invalid";
  try {
    const signature = Buffer.from(history.signatures.signature, "base64");
    if (signature.toString("base64") !== history.signatures.signature || signature.length !== 64) return "issuer_history_signature_invalid";
    if (!verify(null, digest, publicKeyFromRaw(rawEd25519FromMultikey(rootTrust.publicKeyMultibase)), signature)) return "issuer_history_signature_invalid";
  } catch { return "issuer_history_signature_invalid"; }
  return "accepted";
}

function verifyAppendOnly(previous, next) {
  const previousPublishedAt = Date.parse(previous.publishedAt);
  const nextPublishedAt = Date.parse(next.publishedAt);
  if (!Number.isFinite(previousPublishedAt) || !Number.isFinite(nextPublishedAt) || next.sequence !== previous.sequence + 1 || next.previousHistoryRef !== previous.historyId || next.refreshServiceBaseUrl !== previous.refreshServiceBaseUrl || nextPublishedAt <= previousPublishedAt) return "issuer_history_predecessor_invalid";
  const nextKeys = new Map(next.keys.map((key) => [key.keyId, key]));
  for (const prior of previous.keys) {
    const candidate = nextKeys.get(prior.keyId);
    if (!candidate || candidate.verificationMethod !== prior.verificationMethod || candidate.publicKeyMultibase !== prior.publicKeyMultibase || candidate.validFrom !== prior.validFrom || JSON.stringify(candidate.authorizedArtifactTypes) !== JSON.stringify(prior.authorizedArtifactTypes) || JSON.stringify(candidate.authorizedProofPurposes) !== JSON.stringify(prior.authorizedProofPurposes) || !validUntilTightens(prior.validUntil, candidate.validUntil)) return "issuer_history_append_only_invalid";
  }
  return "accepted";
}

function selectHistory(resolver) {
  const { trustRoot, historyChain, selectedHistoryRef, highWaterPersistence } = resolver;
  if (!trustRoot || trustRoot.fixtureClass !== "OUT_OF_BAND_PINNED_ISSUER_HISTORY_TRUST_ROOT") return { code: "issuer_history_unpinned" };
  const byRef = new Map();
  for (const history of historyChain) {
    const result = verifyHistory(history, trustRoot);
    if (result !== "accepted") return { code: result };
    if (byRef.has(history.historyId)) return { code: "issuer_history_equivocation" };
    byRef.set(history.historyId, history);
  }
  const sequences = new Map();
  for (const history of historyChain) {
    if (sequences.has(history.sequence) && sequences.get(history.sequence) !== history.historyId) return { code: "issuer_history_equivocation" };
    sequences.set(history.sequence, history.historyId);
  }
  const bootstrap = byRef.get(trustRoot.pinnedHistoryRef);
  const selected = byRef.get(selectedHistoryRef);
  if (!bootstrap || bootstrap.sequence !== trustRoot.minimumSequence || bootstrap.previousHistoryRef !== null || !selected) return { code: "issuer_history_unpinned" };
  if (selected.sequence < trustRoot.highestAccepted.sequence || (selected.sequence === trustRoot.highestAccepted.sequence && selected.historyId !== trustRoot.highestAccepted.historyRef)) return { code: "issuer_history_rollback" };
  let cursor = selected;
  const selectedChainRefs = new Set([selected.historyId]);
  while (cursor.sequence > bootstrap.sequence) {
    const previous = byRef.get(cursor.previousHistoryRef);
    if (!previous) return { code: "issuer_history_predecessor_invalid" };
    const appendResult = verifyAppendOnly(previous, cursor);
    if (appendResult !== "accepted") return { code: appendResult };
    selectedChainRefs.add(previous.historyId);
    cursor = previous;
  }
  if (cursor.historyId !== bootstrap.historyId) return { code: "issuer_history_predecessor_invalid" };
  const greatestSuppliedSequence = Math.max(...historyChain.map((history) => history.sequence));
  if (selected.sequence !== greatestSuppliedSequence || selectedChainRefs.size !== byRef.size) return { code: "issuer_history_selection_invalid" };
  if (selected.sequence > trustRoot.highestAccepted.sequence) {
    if (highWaterPersistence?.result === "CONFLICT") return { code: "issuer_history_state_conflict" };
    if (!highWaterPersistence?.durable || highWaterPersistence.result !== "SUCCESS") return { code: "issuer_history_state_unavailable" };
    trustRoot.highestAccepted = { sequence: selected.sequence, historyRef: selected.historyId };
  }
  return { code: "accepted", selected, byRef, selectedChainRefs };
}

function evaluate(credential, resolver) {
  const selection = selectHistory(resolver);
  if (selection.code !== "accepted") return selection.code;
  if (!validateDraft("credential", credential)) return "credential_schema_invalid";
  const currentHistory = selection.selected;
  if (credential.issuer !== currentHistory.issuer) return "issuer_invalid";
  const subject = credential.credentialSubject;
  if (["wallet", "recipientId", "holderBinding", "holderKey", "holderPublicKey", "zk", "witness"].some((key) => Object.hasOwn(subject, key))) return "subject_forbidden_property";
  if (!["HARD_VERIFIED", "CORRECTED"].includes(subject.verificationState)) return "issuance_state_invalid";
  if (subject.id !== subjectId(subject) || credential.validFrom !== subject.occurredAt) return "subject_identity_invalid";
  const native = nativeVector.valid.unsignedToken;
  const nativeHash = `sha256:${sha256(Buffer.from(canonicalize(native), "utf8")).toString("hex")}`;
  if (credential.id !== `urn:crinkl:token:${nativeHash}` || nativeHash !== nativeVector.valid.expectedTokenHash) return "native_token_link_invalid";
  if (subject.spendId !== native.spendId || subject.verificationState !== native.canonical.status || subject.storeHash !== native.canonical.storeHash || subject.occurredAt !== native.canonical.timestamp || subject.totalCents !== native.canonical.totalCents || subject.currency !== native.canonical.currency || subject.verificationVersion !== native.canonical.verificationVersion || subject.protocolVersion !== native.protocol.protocolVersion || subject.lineage.headEventHash !== native.lineage.headEventHash || subject.lineage.eventCount !== native.lineage.eventCount || subject.spendStreamNamespaceRef !== vector.nativeSource.spendStreamNamespaceRef || subject.issuerId !== vector.nativeSource.issuerId) return "native_token_mapping_invalid";
  if (JSON.stringify(credential.proof["@context"]) !== JSON.stringify(credential["@context"])) return "proof_context_invalid";
  if (credential.proof.type !== "DataIntegrityProof" || credential.proof.cryptosuite !== "eddsa-jcs-2022" || credential.proof.proofPurpose !== "assertionMethod") return "proof_purpose_invalid";
  const proofCreated = Date.parse(credential.proof.created);
  const occurredAt = Date.parse(subject.occurredAt);
  if (!Number.isFinite(proofCreated) || !Number.isFinite(occurredAt) || proofCreated < occurredAt) return "proof_time_invalid";
  const issuanceHistory = selection.byRef.get(credential.proof.issuerHistoryRef);
  if (!issuanceHistory) return "issuer_history_reference_unknown";
  if (!selection.selectedChainRefs.has(issuanceHistory.historyId)) return "issuer_history_reference_not_selected";
  const issuancePublishedAt = Date.parse(issuanceHistory.publishedAt);
  if (!Number.isFinite(issuancePublishedAt) || issuancePublishedAt > proofCreated) return "issuer_history_time_invalid";
  const issuanceKey = issuanceHistory.keys.find((entry) => entry.verificationMethod === credential.proof.verificationMethod);
  if (!issuanceKey) return "verification_method_unknown";
  if (!issuanceKey.verificationMethod.startsWith(`${issuanceHistory.issuer}#`)) return "issuer_key_controller_invalid";
  try {
    const signature = base58Decode(credential.proof.proofValue.slice(1));
    if (signature.length !== 64 || `z${base58Encode(signature)}` !== credential.proof.proofValue || !verify(null, proofHashData(credential), publicKeyFromRaw(rawEd25519FromMultikey(issuanceKey.publicKeyMultibase)), signature)) return "proof_invalid";
  } catch { return "proof_invalid"; }
  const currentKey = currentHistory.keys.find((entry) => entry.verificationMethod === credential.proof.verificationMethod);
  if (!currentKey) return "issuer_key_not_retained";
  if (currentKey.keyId !== issuanceKey.keyId || currentKey.publicKeyMultibase !== issuanceKey.publicKeyMultibase || currentKey.validFrom !== issuanceKey.validFrom || JSON.stringify(currentKey.authorizedArtifactTypes) !== JSON.stringify(issuanceKey.authorizedArtifactTypes) || JSON.stringify(currentKey.authorizedProofPurposes) !== JSON.stringify(issuanceKey.authorizedProofPurposes)) return "issuer_key_continuity_invalid";
  const issuanceValidFrom = Date.parse(issuanceKey.validFrom);
  const issuanceValidUntil = issuanceKey.validUntil === null ? Number.POSITIVE_INFINITY : Date.parse(issuanceKey.validUntil);
  const currentValidFrom = Date.parse(currentKey.validFrom);
  const currentValidUntil = currentKey.validUntil === null ? Number.POSITIVE_INFINITY : Date.parse(currentKey.validUntil);
  if (!Number.isFinite(issuanceValidFrom) || (issuanceKey.validUntil !== null && !Number.isFinite(issuanceValidUntil)) || !Number.isFinite(currentValidFrom) || (currentKey.validUntil !== null && !Number.isFinite(currentValidUntil)) || proofCreated < issuanceValidFrom || proofCreated >= issuanceValidUntil || proofCreated < currentValidFrom || proofCreated >= currentValidUntil) return "issuer_key_time_invalid";
  if (!issuanceKey.authorizedArtifactTypes.includes("SPEND_ATTESTATION_CREDENTIAL")) return "issuer_key_scope_invalid";
  if (!issuanceKey.authorizedProofPurposes.includes("assertionMethod")) return "issuer_key_purpose_invalid";
  const statusFixture = resolver.status;
  if (!statusFixture?.statusLists?.revocation || !statusFixture.statusLists?.refresh) return "status_indeterminate";
  const [revocation, refresh] = credential.credentialStatus;
  for (const [entry, purpose] of [[revocation, "revocation"], [refresh, "refresh"]]) {
    const result = verifySignedStatusEntry({ entry, purpose, resolver: statusFixture, pinnedResolverSnapshotHash: resolver.statusSnapshotHash, trustRoot: resolver.trustRoot, historyChain: resolver.historyChain, selectedHistoryRef: resolver.selectedHistoryRef });
    if (result === "revoked" || result === "refresh_required") return result;
    if (result === "status_list_unavailable") return "status_indeterminate";
    if (result !== "accepted") return "status_resolution_invalid";
  }
  if (credential.refreshService.type !== "CrinklSpendHeadRefresh" || credential.refreshService.id !== refreshUrl(subject, issuanceHistory)) return "refresh_service_invalid";
  return "accepted";
}

const statusCredentialsByFixture = new Map([
  ["bitstring-status-list-revocation-clear.v1.json", revocationClear],
  ["bitstring-status-list-revocation-set.v1.json", revocationSet],
  ["bitstring-status-list-refresh-clear.v1.json", refreshClear],
  ["bitstring-status-list-refresh-set.v1.json", refreshSet]
]);

function hydratedStatusResolver() {
  const resolver = structuredClone(status);
  for (const resolution of Object.values(resolver.statusLists)) {
    for (const retained of resolution.retainedVersions) retained.credential = structuredClone(statusCredentialsByFixture.get(retained.credentialFixture));
  }
  return resolver;
}

function baseResolver() {
  const hydratedStatus = hydratedStatusResolver();
  assert(statusResolverSnapshotHash(hydratedStatus) === statusVector.pinnedResolverSnapshotHash, "baseline status resolver does not match caller-pinned snapshot");
  return { trustRoot: structuredClone(trustRoot), historyChain: [structuredClone(bootstrapHistory), structuredClone(currentHistory), structuredClone(statusHistory)], selectedHistoryRef: statusHistory.historyId, highWaterPersistence: { durable: true, result: "SUCCESS" }, status: hydratedStatus, statusSnapshotHash: statusVector.pinnedResolverSnapshotHash };
}

function addSelectedSuccessor(resolver) {
  const successor = structuredClone(statusHistory);
  successor.sequence = statusHistory.sequence + 1;
  successor.previousHistoryRef = statusHistory.historyId;
  successor.publishedAt = "2026-08-07T15:00:00.000Z";
  signHistory(successor, vector.issuerKeyMaterial.historyRootPrivateKeySeedHex, resolver.trustRoot.verificationMethod);
  resolver.historyChain.push(successor);
  resolver.selectedHistoryRef = successor.historyId;
  return successor;
}

assert(vector.kind === "credential.spendAttestation.vcdm2.eddsaJcs2022", "unexpected vector kind");
assert(vector.nativeSource.contextClass === "AUTHENTICATED_CANONICAL_HEAD_CONTEXT", "native source context class mismatch");
assert(contextFile["@context"]?.["@protected"] === true && contextFile["@context"]?.totalCents?.["@type"] === "http://www.w3.org/2001/XMLSchema#string" && contextFile["@context"]?.issuerHistoryRef?.["@id"] === "https://crinkl.xyz/ns/spend/v1#issuerHistoryRef" && contextFile["@context"]?.issuerHistoryRef?.["@type"] === "@id", "context mapping mismatch");
execFileSync("python3", [schemaHelper, "--check"], { stdio: "inherit" });
assert(exactKeys(trustRoot, ["fixtureClass", "issuer", "verificationMethod", "publicKeyMultibase", "pinnedHistoryRef", "minimumSequence", "highestAccepted"]) && exactKeys(trustRoot.highestAccepted, ["sequence", "historyRef"]), "trust-root fixture shape mismatch");
assert(trustRoot.pinnedHistoryRef === bootstrapHistory.historyId && trustRoot.highestAccepted.sequence === statusHistory.sequence && trustRoot.highestAccepted.historyRef === statusHistory.historyId, "trust-root pin mismatch");
assert(trustRoot.publicKeyMultibase === multikeyFromRawEd25519(Buffer.from(vector.issuerKeyMaterial.historyRootPublicKeyBase64, "base64")), "history-root public key mismatch");
assert(rawPublicKeyFromSeed(vector.issuerKeyMaterial.historyRootPrivateKeySeedHex).toString("base64") === vector.issuerKeyMaterial.historyRootPublicKeyBase64, "history-root seed mismatch");
assert(rawPublicKeyFromSeed(vector.issuerKeyMaterial.historicalPrivateKeySeedHex).toString("base64") === vector.issuerKeyMaterial.historicalPublicKeyBase64, "historical proof-key seed mismatch");
assert(rawPublicKeyFromSeed(vector.issuerKeyMaterial.currentPrivateKeySeedHex).toString("base64") === vector.issuerKeyMaterial.currentPublicKeyBase64, "current proof-key seed mismatch");
assert(bootstrapHistory.keys[0].publicKeyMultibase === multikeyFromRawEd25519(Buffer.from(vector.issuerKeyMaterial.historicalPublicKeyBase64, "base64")), "bootstrap historical key mismatch");
assert(currentHistory.keys[0].publicKeyMultibase === bootstrapHistory.keys[0].publicKeyMultibase && currentHistory.keys[1].publicKeyMultibase === multikeyFromRawEd25519(Buffer.from(vector.issuerKeyMaterial.currentPublicKeyBase64, "base64")), "current history key mismatch");
assert(JSON.stringify(statusHistory.keys.slice(0, currentHistory.keys.length)) === JSON.stringify(currentHistory.keys) && statusHistory.sequence === currentHistory.sequence + 1 && statusHistory.previousHistoryRef === currentHistory.historyId, "status history must append to current history without changing prior keys");
assert(trustRoot.verificationMethod !== bootstrapHistory.keys[0].verificationMethod && trustRoot.publicKeyMultibase !== bootstrapHistory.keys[0].publicKeyMultibase, "history root and proof key roles must differ");
assert(did.verificationMethod.length === 2 && did.verificationMethod[0].id === currentHistory.keys[1].verificationMethod && did.verificationMethod[0].publicKeyMultibase === currentHistory.keys[1].publicKeyMultibase && did.verificationMethod[1].id === statusHistory.keys[2].verificationMethod && did.verificationMethod[1].publicKeyMultibase === statusHistory.keys[2].publicKeyMultibase && did.assertionMethod.includes(currentHistory.keys[1].verificationMethod) && did.assertionMethod.includes(statusHistory.keys[2].verificationMethod), "current DID/history discovery mismatch");
const credential = vector.valid.credential;
const credentialKey = privateKeyFromSeed(vector.issuerKeyMaterial.historicalPrivateKeySeedHex);
const currentCredentialKey = privateKeyFromSeed(vector.issuerKeyMaterial.currentPrivateKeySeedHex);
assert(credential.proof.proofValue === `z${base58Encode(sign(null, proofHashData(credential), credentialKey))}`, "deterministic credential proof mismatch");
const withoutContext = structuredClone(credential);
delete withoutContext.proof["@context"];
assert(vector.valid.expectedProofValueWithoutContext === `z${base58Encode(sign(null, proofHashData(withoutContext), credentialKey))}`, "context-copy diagnostic mismatch");
assert(evaluate(credential, baseResolver()) === "accepted", `valid credential rejected: ${evaluate(credential, baseResolver())}`);

for (const rejectCase of vector.rejectCases) {
  const candidate = structuredClone(credential);
  applyMutation(candidate, rejectCase.mutation, vector.valid);
  if (rejectCase.resign) candidate.proof.proofValue = `z${base58Encode(sign(null, proofHashData(candidate), credentialKey))}`;
  assert(evaluate(candidate, baseResolver()) === rejectCase.expectedCode, `${rejectCase.id} result mismatch`);
}
for (const resolverCase of vector.resolverCases) {
  const resolver = baseResolver();
  const candidate = structuredClone(credential);
  if (resolverCase.credentialMutation) applyMutation(candidate, resolverCase.credentialMutation, vector.valid);
  if (resolverCase.resolverMutation) applyMutation(resolver[resolverCase.resolverTarget], resolverCase.resolverMutation, vector.valid);
  if (resolverCase.resolverTarget === "status") resolver.statusSnapshotHash = statusResolverSnapshotHash(resolver.status);
  if (resolverCase.resign) candidate.proof.proofValue = `z${base58Encode(sign(null, proofHashData(candidate), credentialKey))}`;
  assert(evaluate(candidate, resolver) === resolverCase.expectedCode, `${resolverCase.id} result mismatch`);
}
for (const historyCase of vector.historyChainCases) {
  const resolver = baseResolver();
  const candidate = structuredClone(credential);
  const rootSeed = vector.issuerKeyMaterial.historyRootPrivateKeySeedHex;
  if (historyCase.mode === "tampered-signature") resolver.historyChain[1].signatures.signature = `A${resolver.historyChain[1].signatures.signature.slice(1)}`;
  if (historyCase.mode === "tampered-hash") resolver.historyChain[1].historyId = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  if (historyCase.mode === "unpinned") resolver.trustRoot.pinnedHistoryRef = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
  if (historyCase.mode === "rollback") resolver.selectedHistoryRef = bootstrapHistory.historyId;
  if (historyCase.mode === "broken-predecessor") { resolver.historyChain[1].previousHistoryRef = "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "equivocation") { const other = structuredClone(resolver.historyChain[1]); other.refreshServiceBaseUrl = "https://equivocation.example"; signHistory(other, rootSeed, resolver.trustRoot.verificationMethod); resolver.historyChain.push(other); }
  if (historyCase.mode === "root-proof-confusion") signHistory(resolver.historyChain[1], vector.issuerKeyMaterial.historicalPrivateKeySeedHex, vector.valid.credential.proof.verificationMethod);
  if (historyCase.mode === "append-only") { resolver.historyChain[1].keys[0].publicKeyMultibase = resolver.trustRoot.publicKeyMultibase; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "tightened-valid-until") { resolver.historyChain[1].keys[0].validUntil = "2026-08-07T12:01:00.000Z"; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "history-no-millisecond-time") { resolver.historyChain[1].publishedAt = "2026-08-07T13:00:00Z"; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "artifact-scope-denial") { resolver.historyChain[1].keys[1].authorizedArtifactTypes = ["OTHER_ARTIFACT"]; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "proof-purpose-denial") { resolver.historyChain[1].keys[1].authorizedProofPurposes = ["authentication"]; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "non-increasing-published-at") { resolver.historyChain[1].publishedAt = bootstrapHistory.publishedAt; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "duplicate-key-identity") { resolver.historyChain[1].keys.push(structuredClone(resolver.historyChain[1].keys[1])); signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "public-key-reauthorization") { const alias = structuredClone(resolver.historyChain[1].keys[1]); alias.keyId = "spend-attestation-2026-09"; alias.verificationMethod = "did:web:vc-test.example#spend-attestation-2026-09"; alias.publicKeyMultibase = resolver.historyChain[1].keys[0].publicKeyMultibase; resolver.historyChain[1].keys.push(alias); signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "invalid-calendar-history-time") { resolver.historyChain[1].publishedAt = "2026-99-99T99:99:99.999Z"; signHistory(resolver.historyChain[1], rootSeed, resolver.trustRoot.verificationMethod); resolver.selectedHistoryRef = resolver.historyChain[1].historyId; resolver.trustRoot.highestAccepted.historyRef = resolver.historyChain[1].historyId; }
  if (historyCase.mode === "side-branch-issuance") {
    const sideBranch = structuredClone(currentHistory);
    sideBranch.sequence = 3;
    sideBranch.previousHistoryRef = bootstrapHistory.historyId;
    sideBranch.publishedAt = "2026-08-07T13:00:30.000Z";
    sideBranch.keys = [{ ...sideBranch.keys[1], publicKeyMultibase: sideBranch.keys[0].publicKeyMultibase }];
    signHistory(sideBranch, rootSeed, resolver.trustRoot.verificationMethod);
    resolver.historyChain.push(sideBranch);
    candidate.proof.verificationMethod = sideBranch.keys[0].verificationMethod;
    candidate.proof.created = "2026-08-07T13:01:00.000Z";
    candidate.proof.issuerHistoryRef = sideBranch.historyId;
    candidate.proof.proofValue = `z${base58Encode(sign(null, proofHashData(candidate), credentialKey))}`;
  }
  if (["broken-predecessor", "append-only", "tightened-valid-until", "history-no-millisecond-time", "artifact-scope-denial", "proof-purpose-denial", "non-increasing-published-at", "duplicate-key-identity", "public-key-reauthorization", "invalid-calendar-history-time"].includes(historyCase.mode)) {
    const selectedStatusHistory = resolver.historyChain[2];
    selectedStatusHistory.previousHistoryRef = resolver.historyChain[1].historyId;
    selectedStatusHistory.keys = [...structuredClone(resolver.historyChain[1].keys), structuredClone(statusHistory.keys[2])];
    signHistory(selectedStatusHistory, rootSeed, resolver.trustRoot.verificationMethod);
    resolver.selectedHistoryRef = selectedStatusHistory.historyId;
    resolver.trustRoot.highestAccepted = { sequence: selectedStatusHistory.sequence, historyRef: selectedStatusHistory.historyId };
  }
  if (["artifact-scope-denial", "proof-purpose-denial"].includes(historyCase.mode)) {
    candidate.proof.verificationMethod = "did:web:vc-test.example#spend-attestation-2026-08";
    candidate.proof.created = "2026-08-07T13:01:00.000Z";
    candidate.proof.issuerHistoryRef = resolver.historyChain[1].historyId;
    candidate.proof.proofValue = `z${base58Encode(sign(null, proofHashData(candidate), currentCredentialKey))}`;
  }
  if (historyCase.mode === "future-issuance-history") {
    candidate.proof.issuerHistoryRef = currentHistory.historyId;
    candidate.proof.proofValue = `z${base58Encode(sign(null, proofHashData(candidate), credentialKey))}`;
  }
  const historyResult = evaluate(candidate, resolver);
  assert(historyResult === historyCase.expectedCode, `${historyCase.id} expected ${historyCase.expectedCode}, received ${historyResult}`);
}
for (const stateCase of vector.historyStateCases) {
  const resolver = baseResolver();
  const successor = addSelectedSuccessor(resolver);
  const candidate = structuredClone(credential);
  resolver.highWaterPersistence.durable = stateCase.durable !== false;
  resolver.highWaterPersistence.result = stateCase.persistenceResult;
  if (stateCase.mode === "invalid-credential") candidate.proof.proofValue = `z${"1".repeat(64)}`;
  if (stateCase.mode === "schema-invalid-credential") candidate.unexpected = true;
  assert(evaluate(candidate, resolver) === stateCase.expectedCode, `${stateCase.id} result mismatch`);
  if (stateCase.expectAdvanced) assert(resolver.trustRoot.highestAccepted.sequence === successor.sequence && resolver.trustRoot.highestAccepted.historyRef === successor.historyId, `${stateCase.id} did not advance durable high-water state`);
  else assert(resolver.trustRoot.highestAccepted.sequence === statusHistory.sequence && resolver.trustRoot.highestAccepted.historyRef === statusHistory.historyId, `${stateCase.id} changed high-water state after failed persistence`);
  if (stateCase.restartExpectedCode) {
    const restarted = baseResolver();
    restarted.trustRoot.highestAccepted = structuredClone(resolver.trustRoot.highestAccepted);
    restarted.historyChain = structuredClone(resolver.historyChain);
    restarted.selectedHistoryRef = successor.historyId;
    restarted.highWaterPersistence = { durable: false, result: "UNKNOWN" };
    assert(evaluate(credential, restarted) === stateCase.restartExpectedCode, `${stateCase.id} restart result mismatch`);
  }
  if (stateCase.retryExpectedCode) {
    resolver.highWaterPersistence = { durable: true, result: "SUCCESS" };
    assert(evaluate(credential, resolver) === stateCase.retryExpectedCode, `${stateCase.id} retry result mismatch`);
    assert(resolver.trustRoot.highestAccepted.sequence === successor.sequence && resolver.trustRoot.highestAccepted.historyRef === successor.historyId, `${stateCase.id} retry did not advance state`);
  }
}
for (const statusCase of vector.statusDecisionCases) {
  const resolver = baseResolver();
  const fixture = statusCase.purpose === "revocation" ? revocationSet : refreshSet;
  const fixtureName = statusCase.purpose === "revocation" ? "bitstring-status-list-revocation-set.v1.json" : "bitstring-status-list-refresh-set.v1.json";
  const resolution = resolver.status.statusLists[statusCase.purpose];
  const hash = credentialHash(fixture);
  resolution.selectedCredentialHash = hash;
  resolution.retainedVersions = [{ credentialHash: hash, credentialFixture: fixtureName, credential: structuredClone(fixture) }];
  resolver.statusSnapshotHash = statusVector.alternativePinnedResolverSnapshotHashes[`${statusCase.purpose}Set`];
  assert(statusResolverSnapshotHash(resolver.status) === resolver.statusSnapshotHash, `${statusCase.id} status snapshot pin mismatch`);
  assert(evaluate(credential, resolver) === statusCase.expectedCode, `${statusCase.id} result mismatch`);
}
console.log(`w3c vc 2.0 fixture harness: 1 accepted, ${vector.rejectCases.length} direct rejects, ${vector.resolverCases.length} resolver cases, ${vector.historyChainCases.length} history-chain cases, ${vector.historyStateCases.length} history-state cases, ${vector.statusDecisionCases.length} status decisions`);
