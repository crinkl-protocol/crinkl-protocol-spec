#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const conformanceRoot = path.join(repoRoot, "conformance", "v1");
const strictCoverage = process.argv.includes("--strict-coverage");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function sha256HexUtf8(value) {
  return crypto.createHash("sha256").update(value, "utf8").digest("hex");
}

function sha256HexBytes(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

// RFC 8785/JCS canonicalization for JSON values used in vectors.
function canonicalizeJson(value) {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error(`non-finite number cannot be canonicalized: ${value}`);
    }
    return JSON.stringify(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalizeJson(item)).join(",")}]`;
  }
  if (typeof value === "object") {
    const keys = Object.keys(value).sort();
    const parts = keys.map((key) => `${JSON.stringify(key)}:${canonicalizeJson(value[key])}`);
    return `{${parts.join(",")}}`;
  }
  throw new Error(`unsupported JSON value type: ${typeof value}`);
}

function ed25519PrivateKeyFromSeedHex(seedHex) {
  const seed = Buffer.from(seedHex, "hex");
  if (seed.length !== 32) throw new Error(`ed25519 seed must be 32 bytes, got ${seed.length}`);
  const pkcs8Prefix = Buffer.from("302e020100300506032b657004220420", "hex");
  const pkcs8 = Buffer.concat([pkcs8Prefix, seed]);
  return crypto.createPrivateKey({ key: pkcs8, format: "der", type: "pkcs8" });
}

function ed25519PublicKeyFromRaw(raw) {
  const rawBytes = Buffer.isBuffer(raw) ? raw : Buffer.from(raw);
  if (rawBytes.length !== 32) throw new Error(`ed25519 public key must be 32 bytes, got ${rawBytes.length}`);
  const spkiPrefix = Buffer.from("302a300506032b6570032100", "hex");
  const spki = Buffer.concat([spkiPrefix, rawBytes]);
  return crypto.createPublicKey({ key: spki, format: "der", type: "spki" });
}

function derivedRawPublicKeyFromPrivate(privateKey) {
  const spki = crypto.createPublicKey(privateKey).export({ format: "der", type: "spki" });
  return Buffer.from(spki).subarray(-32);
}

function deriveMasterSecret(walletSecrets) {
  const sortedSecrets = [...walletSecrets].sort();
  const canonical = canonicalizeJson({ v: 1, walletSecrets: sortedSecrets });
  return sha256HexUtf8(canonical);
}

function deriveNullifier(masterSecretHex, scopeId) {
  const canonical = canonicalizeJson({ masterSecret: masterSecretHex, scopeId, v: 1 });
  return `sha256:${sha256HexUtf8(canonical)}`;
}

function runScenario(events) {
  let attestationState = "NONE";
  let rewardState = "NO_REWARD";

  for (const event of events) {
    const name = event.eventName;
    if (name === "RECEIPT_UPLOADED") attestationState = "UPLOADED";
    if (name === "SPEND_SOFT_VERIFIED") attestationState = "SOFT_VERIFIED";
    if (name === "SPEND_HARD_VERIFIED") attestationState = "HARD_VERIFIED";
    if (name === "SPEND_CORRECTED") attestationState = "CORRECTED";
    if (name === "SPEND_INVALIDATED" || name === "FRAUD_FLAGGED") attestationState = "INVALIDATED";

    if (name === "REWARD_PROVISIONAL_ISSUED" && rewardState === "NO_REWARD") {
      rewardState = "PROVISIONAL_REWARD_ISSUED";
    }
    if (name === "REWARD_FINAL_ISSUED") rewardState = "FINAL_REWARD_ISSUED";
  }

  return { attestationState, rewardState };
}

function fail(failures, kind, caseId, message) {
  failures.push(`[${kind}] ${caseId}: ${message}`);
}

function main() {
  const failures = [];
  const skippedKinds = [];
  const executedKinds = [];
  let checks = 0;

  const manifestPath = path.join(conformanceRoot, "manifest.json");
  const manifest = readJson(manifestPath);

  for (const vectorMeta of manifest.vectors) {
    const kind = vectorMeta.kind;
    const vectorPath = path.join(conformanceRoot, vectorMeta.file);
    const vector = readJson(vectorPath);

    if (vector.kind !== kind) {
      fail(failures, kind, "manifest", `kind mismatch: manifest=${kind}, file=${vector.kind}`);
      continue;
    }

    if (kind === "canonicalization") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const parsed = JSON.parse(c.inputJson);
        const canonical = canonicalizeJson(parsed);
        checks += 1;
        if (canonical !== c.expectedCanonical) {
          fail(failures, kind, c.id, "expectedCanonical mismatch");
        }
        if (typeof c.expectedSha256Hex === "string") {
          const hashHex = sha256HexUtf8(canonical);
          checks += 1;
          if (hashHex !== c.expectedSha256Hex) {
            fail(failures, kind, c.id, "expectedSha256Hex mismatch");
          }
          if (typeof c.expectedSha256Id === "string") {
            const hashId = `sha256:${hashHex}`;
            checks += 1;
            if (hashId !== c.expectedSha256Id) {
              fail(failures, kind, c.id, "expectedSha256Id mismatch");
            }
          }
        }
      }
      continue;
    }

    if (kind === "eventHash") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const event = JSON.parse(c.eventJson);
        const { eventHash: _eventHash, signature: _signature, ...hashInput } = event;
        const canonical = canonicalizeJson(hashInput);
        checks += 1;
        if (canonical !== c.expectedHashInputCanonical) {
          fail(failures, kind, c.id, "expectedHashInputCanonical mismatch");
        }
        const hashHex = sha256HexUtf8(canonical);
        checks += 1;
        if (hashHex !== c.expectedEventHashHex) {
          fail(failures, kind, c.id, "expectedEventHashHex mismatch");
        }
      }
      continue;
    }

    if (kind === "ed25519") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const privateKey = ed25519PrivateKeyFromSeedHex(c.privateKeySeedHex);
        const derivedPublicRaw = derivedRawPublicKeyFromPrivate(privateKey);
        checks += 1;
        if (derivedPublicRaw.toString("hex") !== c.publicKeyHex) {
          fail(failures, kind, c.id, "public key derivation mismatch");
        }

        const publicKey = ed25519PublicKeyFromRaw(Buffer.from(c.publicKeyHex, "hex"));
        const message = Buffer.from(c.messageHex, "hex");
        const expectedSignature = Buffer.from(c.expectedSignatureBase64, "base64");
        const derivedSignature = crypto.sign(null, message, privateKey);
        checks += 1;
        if (!derivedSignature.equals(expectedSignature)) {
          fail(failures, kind, c.id, "signature derivation mismatch");
        }

        const ok = crypto.verify(null, message, publicKey, expectedSignature);
        checks += 1;
        if (!ok) fail(failures, kind, c.id, "signature verification failed");
      }
      continue;
    }

    if (kind === "tokenHash.spendAttestation.v1") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const unsignedToken = JSON.parse(c.unsignedTokenJson);
        const canonical = canonicalizeJson(unsignedToken);
        checks += 1;
        if (canonical !== c.expectedCanonical) {
          fail(failures, kind, c.id, "expectedCanonical mismatch");
        }
        const tokenHashHex = sha256HexUtf8(canonical);
        checks += 1;
        if (tokenHashHex !== c.expectedTokenHashHex) {
          fail(failures, kind, c.id, "expectedTokenHashHex mismatch");
        }
      }
      continue;
    }

    if (kind === "token.spendAttestation.portableV1.fromSpendStream") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const privateKey = ed25519PrivateKeyFromSeedHex(c.issuerPrivateKeySeedHex);
        const derivedPublicRaw = derivedRawPublicKeyFromPrivate(privateKey);
        const derivedPublicB64 = derivedPublicRaw.toString("base64");
        checks += 1;
        if (derivedPublicB64 !== c.issuerPublicKeyBase64) {
          fail(failures, kind, c.id, "issuerPublicKeyBase64 mismatch");
        }

        const expectedToken = c.expectedToken;
        const signatures = expectedToken.signatures || {};
        const unsignedToken = { ...expectedToken };
        delete unsignedToken.signatures;

        const canonicalUnsignedToken = canonicalizeJson(unsignedToken);
        const tokenHashHex = sha256HexUtf8(canonicalUnsignedToken);
        checks += 1;
        if (tokenHashHex !== signatures.tokenHash) {
          fail(failures, kind, c.id, "token hash mismatch");
        }

        const message = Buffer.from(tokenHashHex, "hex");
        const expectedSignature = Buffer.from(signatures.signature, "base64");
        const derivedSignature = crypto.sign(null, message, privateKey);
        checks += 1;
        if (!derivedSignature.equals(expectedSignature)) {
          fail(failures, kind, c.id, "signature mismatch");
        }

        const declaredPublic = Buffer.from(signatures.publicKey, "base64");
        const declaredPublicKey = ed25519PublicKeyFromRaw(declaredPublic);
        const ok = crypto.verify(null, message, declaredPublicKey, expectedSignature);
        checks += 1;
        if (!ok) fail(failures, kind, c.id, "signature verification failed");
      }
      continue;
    }

    if (kind === "token.verifiedSpendDistribution.v1") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const privateKey = ed25519PrivateKeyFromSeedHex(c.issuerPrivateKeySeedHex);
        const derivedPublicRaw = derivedRawPublicKeyFromPrivate(privateKey);
        const derivedPublicB64 = derivedPublicRaw.toString("base64");
        checks += 1;
        if (derivedPublicB64 !== c.issuerPublicKeyBase64) {
          fail(failures, kind, c.id, "issuerPublicKeyBase64 mismatch");
        }

        const expectedToken = c.expectedToken;
        const signatures = expectedToken.signatures || {};
        const unsignedToken = { ...expectedToken };
        delete unsignedToken.signatures;

        const canonicalUnsignedToken = canonicalizeJson(unsignedToken);
        const tokenHashHex = sha256HexUtf8(canonicalUnsignedToken);
        checks += 1;
        if (tokenHashHex !== signatures.tokenHash) {
          fail(failures, kind, c.id, "token hash mismatch");
        }

        const message = Buffer.from(tokenHashHex, "hex");
        const expectedSignature = Buffer.from(signatures.signature, "base64");
        const derivedSignature = crypto.sign(null, message, privateKey);
        checks += 1;
        if (!derivedSignature.equals(expectedSignature)) {
          fail(failures, kind, c.id, "signature mismatch");
        }

        const declaredPublic = Buffer.from(signatures.publicKey, "base64");
        const declaredPublicKey = ed25519PublicKeyFromRaw(declaredPublic);
        const ok = crypto.verify(null, message, declaredPublicKey, expectedSignature);
        checks += 1;
        if (!ok) fail(failures, kind, c.id, "signature verification failed");
      }
      continue;
    }

    if (kind === "scenario.spend.lifecycle") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        const out = runScenario(c.events);
        checks += 1;
        if (out.attestationState !== c.expected.attestationState) {
          fail(failures, kind, c.id, "attestationState mismatch");
        }
        checks += 1;
        if (out.rewardState !== c.expected.rewardState) {
          fail(failures, kind, c.id, "rewardState mismatch");
        }
      }
      continue;
    }

    if (kind === "nullifier.crossWallet") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        if (Array.isArray(c.walletSecrets) && typeof c.scopeId === "string") {
          const masterSecret = deriveMasterSecret(c.walletSecrets);
          checks += 1;
          if (masterSecret !== c.expectedMasterSecretHex) {
            fail(failures, kind, c.id, "expectedMasterSecretHex mismatch");
          }
          if (typeof c.expectedNullifier === "string") {
            const nullifier = deriveNullifier(masterSecret, c.scopeId);
            checks += 1;
            if (nullifier !== c.expectedNullifier) {
              fail(failures, kind, c.id, "expectedNullifier mismatch");
            }
          }
        }
        if (Array.isArray(c.walletSecretsShared) && typeof c.scopeId === "string") {
          const masterSecret = deriveMasterSecret(c.walletSecretsShared);
          checks += 1;
          if (masterSecret !== c.expectedMasterSecretHex) {
            fail(failures, kind, c.id, "walletSecretsShared expectedMasterSecretHex mismatch");
          }
          const nullifier = deriveNullifier(masterSecret, c.scopeId);
          checks += 1;
          if (nullifier !== c.expectedNullifier) {
            fail(failures, kind, c.id, "walletSecretsShared expectedNullifier mismatch");
          }
        }
        if (Array.isArray(c.walletSecretsOrderA) && Array.isArray(c.walletSecretsOrderB)) {
          const msA = deriveMasterSecret(c.walletSecretsOrderA);
          const msB = deriveMasterSecret(c.walletSecretsOrderB);
          checks += 1;
          if (msA !== msB || msA !== c.expectedMasterSecretHex) {
            fail(failures, kind, c.id, "order independence mismatch");
          }
          const nullifier = deriveNullifier(msA, c.scopeId);
          checks += 1;
          if (nullifier !== c.expectedNullifier) {
            fail(failures, kind, c.id, "order independence nullifier mismatch");
          }
        }
        if (Array.isArray(c.walletSecrets) && typeof c.scopeIdA === "string" && typeof c.scopeIdB === "string") {
          const masterSecret = deriveMasterSecret(c.walletSecrets);
          checks += 1;
          if (masterSecret !== c.expectedMasterSecretHex) {
            fail(failures, kind, c.id, "scopeIsolation expectedMasterSecretHex mismatch");
          }
          const nullifierA = deriveNullifier(masterSecret, c.scopeIdA);
          const nullifierB = deriveNullifier(masterSecret, c.scopeIdB);
          checks += 2;
          if (nullifierA !== c.expectedNullifierA) {
            fail(failures, kind, c.id, "scopeIsolation expectedNullifierA mismatch");
          }
          if (nullifierB !== c.expectedNullifierB) {
            fail(failures, kind, c.id, "scopeIsolation expectedNullifierB mismatch");
          }
        }
      }
      continue;
    }

    if (kind === "recipient.blinded.schemaV1b") {
      executedKinds.push(kind);
      for (const c of vector.cases) {
        if (typeof c.walletAddress === "string" && typeof c.blinder === "string" && typeof c.expectedRecipientId === "string") {
          const recipientId = `sha256:${sha256HexUtf8(`${c.walletAddress}${c.blinder}`)}`;
          checks += 1;
          if (recipientId !== c.expectedRecipientId) {
            fail(failures, kind, c.id, "expectedRecipientId mismatch");
          }
        }
        if (typeof c.walletAddress === "string" && typeof c.blinderBatch1 === "string" && typeof c.expectedRecipientIdBatch1 === "string") {
          const recipientId = `sha256:${sha256HexUtf8(`${c.walletAddress}${c.blinderBatch1}`)}`;
          checks += 1;
          if (recipientId !== c.expectedRecipientIdBatch1) {
            fail(failures, kind, c.id, "expectedRecipientIdBatch1 mismatch");
          }
        }
        if (typeof c.walletAddress === "string" && typeof c.blinderBatch2 === "string" && typeof c.expectedRecipientIdBatch2 === "string") {
          const recipientId = `sha256:${sha256HexUtf8(`${c.walletAddress}${c.blinderBatch2}`)}`;
          checks += 1;
          if (recipientId !== c.expectedRecipientIdBatch2) {
            fail(failures, kind, c.id, "expectedRecipientIdBatch2 mismatch");
          }
        }
        if (typeof c.walletAddress === "string" && typeof c.blinderIdentityA === "string" && typeof c.expectedRecipientIdA === "string") {
          const recipientId = `sha256:${sha256HexUtf8(`${c.walletAddress}${c.blinderIdentityA}`)}`;
          checks += 1;
          if (recipientId !== c.expectedRecipientIdA) {
            fail(failures, kind, c.id, "expectedRecipientIdA mismatch");
          }
        }
        if (typeof c.walletAddress === "string" && typeof c.blinderIdentityB === "string" && typeof c.expectedRecipientIdB === "string") {
          const recipientId = `sha256:${sha256HexUtf8(`${c.walletAddress}${c.blinderIdentityB}`)}`;
          checks += 1;
          if (recipientId !== c.expectedRecipientIdB) {
            fail(failures, kind, c.id, "expectedRecipientIdB mismatch");
          }
        }
        if (c.openingProof?.wallet && c.openingProof?.blinder && c.openingProof?.recomputedRecipientId) {
          const recomputed = `sha256:${sha256HexUtf8(`${c.openingProof.wallet}${c.openingProof.blinder}`)}`;
          checks += 1;
          if (recomputed !== c.openingProof.recomputedRecipientId) {
            fail(failures, kind, c.id, "openingProof recomputedRecipientId mismatch");
          }
        }
        if (typeof c.expectedLeafCanonical === "string") {
          let leaf = null;
          if (c.expectedAggregatedLeaf) leaf = c.expectedAggregatedLeaf;
          if (c.expectedLinkableLeaf) leaf = c.expectedLinkableLeaf;
          if (!leaf && c.batchId && c.totalPoints && c.expectedRecipientId) {
            leaf = {
              batchId: c.batchId,
              recipientId: c.expectedRecipientId,
              totalPoints: c.totalPoints
            };
          }
          if (leaf) {
            const canonical = canonicalizeJson(leaf);
            checks += 1;
            if (canonical !== c.expectedLeafCanonical) {
              fail(failures, kind, c.id, "expectedLeafCanonical mismatch");
            }
          }
        }
      }
      continue;
    }

    skippedKinds.push({
      kind,
      reason: "no executable verifier in scripts/verify_conformance.mjs yet"
    });
  }

  if (failures.length > 0) {
    console.error("[conformance] FAIL");
    for (const failure of failures) console.error(` - ${failure}`);
    process.exit(1);
  }

  console.log("[conformance] OK");
  console.log(` - checks: ${checks}`);
  console.log(` - executed kinds: ${executedKinds.sort().join(", ")}`);
  if (skippedKinds.length > 0) {
    console.log(` - skipped kinds: ${skippedKinds.map((x) => x.kind).join(", ")}`);
    if (strictCoverage) {
      console.error("[conformance] strict coverage enabled and skipped kinds remain");
      process.exit(2);
    }
  }
}

main();
