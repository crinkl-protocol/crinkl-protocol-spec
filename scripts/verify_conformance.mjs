#!/usr/bin/env node

import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const conformanceRoot = path.join(repoRoot, "07-conformance", "vectors", "v1");
const strictCoverage = process.argv.includes("--strict-coverage");
const requireReleased = process.argv.includes("--require-released");
const requiredKinds = new Set();
for (let index = 2; index < process.argv.length; index += 1) {
  if (process.argv[index] !== "--require-kind") continue;
  const kind = process.argv[index + 1];
  if (!kind || kind.startsWith("--")) {
    throw new Error("--require-kind requires one manifest kind");
  }
  requiredKinds.add(kind);
  index += 1;
}

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

function isWithin(root, candidate) {
  return candidate === root || candidate.startsWith(`${root}${path.sep}`);
}

function runExternalVerifier(vectorMeta) {
  const verifier = vectorMeta.externalVerifier || {};
  if (
    !["python3", "node"].includes(verifier.type) ||
    typeof verifier.file !== "string"
  ) {
    throw new Error(`unsupported external verifier descriptor for ${vectorMeta.kind}`);
  }

  const profilesRoot = path.resolve(repoRoot, "07-conformance", "profiles");
  const verifierPath = path.resolve(conformanceRoot, verifier.file);
  if (!isWithin(profilesRoot, verifierPath)) {
    throw new Error(`external verifier escapes released profile root: ${verifier.file}`);
  }
  if (!fs.statSync(verifierPath).isFile()) {
    throw new Error(`external verifier is not a file: ${verifier.file}`);
  }

  const timeout = vectorMeta.kind === "credential.spendAttestation.vcdm2.eddsaJcs2022"
    ? 180_000
    : 60_000;

  return spawnSync(verifier.type, [verifierPath], {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    timeout,
    maxBuffer: 1024 * 1024
  });
}

function main() {
  const failures = [];
  const dataOnlyKinds = [];
  const executedKinds = [];
  let checks = 0;

  const releaseManifest = readJson(path.join(repoRoot, "versions", "release.json"));
  if (requireReleased && releaseManifest.status !== "RELEASED") {
    console.error(
      `[conformance] release required but status=${releaseManifest.status || "MISSING"}`
    );
    process.exit(4);
  }

  const manifestPath = path.join(conformanceRoot, "manifest.json");
  const manifest = readJson(manifestPath);

  for (const vectorMeta of manifest.vectors) {
    const kind = vectorMeta.kind;
    const vectorPath = path.resolve(conformanceRoot, vectorMeta.file);
    const profilesRoot = path.resolve(repoRoot, "07-conformance", "profiles");
    if (!isWithin(conformanceRoot, vectorPath) && !isWithin(profilesRoot, vectorPath)) {
      fail(failures, kind, "manifest", `vector escapes conformance roots: ${vectorMeta.file}`);
      continue;
    }
    const vector = readJson(vectorPath);

    if (vector.kind !== kind) {
      fail(failures, kind, "manifest", `kind mismatch: manifest=${kind}, file=${vector.kind}`);
      continue;
    }

    if (vectorMeta.externalVerifier) {
      let result;
      try {
        result = runExternalVerifier(vectorMeta);
      } catch (error) {
        fail(failures, kind, "external-verifier", error.message);
        continue;
      }
      checks += 1;
      if (result.status !== 0) {
        const detail = `${result.stderr || ""}\n${result.stdout || ""}`.trim();
        fail(
          failures,
          kind,
          "external-verifier",
          `exit=${result.status} ${detail}`.trim()
        );
        continue;
      }
      executedKinds.push(kind);
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

    if (kind === "token.spendAttestation.portableV1.fromSpendStream.v2") {
      executedKinds.push(kind);
      const adopted = vector.adoptedCandidate || {};
      checks += 1;
      if (adopted.repository !== "crinkl-protocol" || adopted.commit !== "093b37db3e78bdd4253d7864ae4eb5398ce7cc25" || adopted.artifact?.path !== "protocol/portability/TOKENS.md" || adopted.artifact?.sha256 !== "sha256:e094a25cb91ba43053c7deeb8299c7e544268a6155a5d7e83ab324eac694df34") {
        fail(failures, kind, "adopted-candidate", "adopted candidate pin mismatch");
      }
      const compatibility = vector.compatibility || {};
      checks += 1;
      if (compatibility.legacyVectorKind !== "token.spendAttestation.portableV1.fromSpendStream" || compatibility.legacyVectorState !== "IMMUTABLE_RELEASED_RC7_EVIDENCE" || compatibility.signedTokenSchemaChange !== false || compatibility.wireProtocolChange !== false) {
        fail(failures, kind, "compatibility", "legacy/signed-wire boundary mismatch");
      }
      const supersessionCases = vector.supersessionCases;
      const referenceInclusionCases = vector.referenceInclusionCases;
      checks += 1;
      if (!Array.isArray(supersessionCases) || supersessionCases.length !== 3) fail(failures, kind, "supersession-cases", "requires exactly three nonempty issuer-scope cases");
      checks += 1;
      if (!Array.isArray(referenceInclusionCases) || referenceInclusionCases.length !== 2) fail(failures, kind, "reference-inclusion-cases", "requires exactly two nonempty audit-independence cases");
      for (const c of supersessionCases || []) {
        const [first, second] = c.tokens || [];
        const wellFormed = [first, second].every((token) => token && typeof token.signatures?.issuedBy === "string" && token.signatures.issuedBy.length > 0 && typeof token.spendId === "string" && Number.isInteger(token.eventCount) && /^[0-9a-f]{64}$/.test(token.headEventHash) && typeof token.status === "string");
        checks += 1;
        if (!wellFormed) fail(failures, kind, c.id, "supersession token shape mismatch");
        if (c.id === "issuer-scoped-newest") {
          checks += 1;
          if (first.signatures.issuedBy !== second.signatures.issuedBy || first.spendId !== second.spendId || second.eventCount <= first.eventCount || c.expected !== "SECOND_TOKEN_NEWEST") fail(failures, kind, c.id, "issuer-scoped newest mismatch");
        } else if (c.id === "different-issuers-do-not-compete") {
          checks += 1;
          if (first.signatures.issuedBy === second.signatures.issuedBy || first.spendId !== second.spendId || c.expected !== "TWO_DISTINCT_SUPERSESSION_SETS") fail(failures, kind, c.id, "cross-issuer scope mismatch");
        } else if (c.id === "issuer-scoped-equal-count-fork") {
          checks += 1;
          if (first.signatures.issuedBy !== second.signatures.issuedBy || first.spendId !== second.spendId || first.eventCount !== second.eventCount || (first.headEventHash === second.headEventHash && first.status === second.status) || c.expected !== "ORDERING_VIOLATION") fail(failures, kind, c.id, "issuer-scoped fork mismatch");
        } else {
          fail(failures, kind, c.id || "unknown", "unknown supersession case");
        }
      }
      for (const c of referenceInclusionCases || []) {
        const proof = c.proof || {};
        const leaf = proof.leaf || {};
        const canonical = canonicalizeJson(leaf);
        const leafHash = sha256HexBytes(Buffer.concat([Buffer.from([0]), Buffer.from(canonical, "utf8")]));
        checks += 1;
        if (Object.keys(leaf).sort().join(",") !== "rewardEventHash,spendId" || !/^[0-9a-f]{64}$/.test(leaf.rewardEventHash) || leafHash !== proof.leafHash || proof.rewardEventsRoot !== proof.leafHash) fail(failures, kind, c.id, "reference inclusion proof mismatch");
        checks += 1;
        if (c.expected?.referenceInclusion !== true || !["ABSENT", "INVALID"].includes(c.audit) || c.expected?.auditOutcome !== (c.audit === "ABSENT" ? "UNAVAILABLE" : "INVALID")) fail(failures, kind, c.id, "independent audit outcome mismatch");
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

    dataOnlyKinds.push({
      kind,
      reason: "no executable verifier in scripts/verify_conformance.mjs yet"
    });
  }

  if (failures.length > 0) {
    console.error("[conformance] FAIL");
    for (const failure of failures) console.error(` - ${failure}`);
    process.exit(1);
  }

  const missingRequiredKinds = [...requiredKinds].filter(
    (kind) => !executedKinds.includes(kind)
  );
  if (missingRequiredKinds.length > 0) {
    console.error(
      `[conformance] required kind(s) not executed: ${missingRequiredKinds.join(", ")}`
    );
    process.exit(3);
  }

  console.log("[conformance] OK");
  console.log(
    ` - release: ${releaseManifest.releaseVersion}/${releaseManifest.status}`
  );
  console.log(` - checks: ${checks}`);
  console.log(
    ` - executed kinds (${executedKinds.length}): ${executedKinds.sort().join(", ")}`
  );
  if (dataOnlyKinds.length > 0) {
    console.log(
      ` - data-only kinds (${dataOnlyKinds.length}): ${dataOnlyKinds.map((x) => x.kind).join(", ")}`
    );
    if (strictCoverage) {
      console.error("[conformance] strict coverage enabled and data-only kinds remain");
      process.exit(2);
    }
  }
}

main();
