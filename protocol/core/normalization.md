---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Normalization

## Normalization

Converts extracted receipt content to canonical form. Rules MUST be deterministic for a given `verificationVersion` to ensure reproducible verification and cross-operator compatibility.

| Field | Normalization |
|-------|---------------|
| storeId | See ../protocol/core/canonicalization.md storeId rules |
| totalCents | Base-10 integer string cents, non-negative |
| currency | ISO 4217 uppercase |
| timestamp | ISO 8601 UTC |
| geoRegion (optional) | ISO 3166-2 subdivision code or ISO 3166-1 alpha-2 country code |
| cbsaCode (optional) | CBSA metro area code or non-metro fallback — derived from store location, not receipt text (see `../protocol/core/canonicalization.md#cbsacode`) |

**Constraint:** Transformations MUST NOT introduce data not present in the submission or derivable from explicit rules (e.g., currency inference from storeId). Synthetic data (e.g., randomly generated timestamps) is forbidden.

**LLM determinism constraint (normative):** If an implementation uses an LLM for normalization, it MUST constrain the model to a closed-choice output space (or an equivalent deterministic mapping) and MUST ensure the resulting canonical fields are reproducible given the same inputs and `verificationVersion`.

## Verification Versioning

Each verification pass MUST record a `verificationVersion` identifier that binds the Spend to:
- Normalization rules in effect at verification time
- Store resolution logic
- Currency inference heuristics (if any)
 - If LLMs are used: the exact model identifier, prompt hash, and choice-set (or output schema) hash used to produce canonical fields

When verification rules change, the protocol increments `verificationVersion`. Old Spends are not re-verified automatically; operators MAY emit `SPEND_CORRECTED` events to apply new rules, preserving original events in the ledger.

**Registry guidance (non-normative):** deployments SHOULD publish a verification registry that maps `verificationVersion` to concrete artifacts (prompt hash, model version, choice-set hash) so auditors can reproduce canonical outputs deterministically.

### protocolVersion vs verificationVersion (normative)

- `protocolVersion` is carried on every event envelope and gates event schema and verification semantics.
- `verificationVersion` is carried in hard verification/correction payloads and gates normalization/resolution semantics for canonical Spend fields.

**Version skew handling (normative):**
- Verifiers MUST reject events whose `protocolVersion` they do not support (`VersionMismatch`).
- Within a single spend-stream (`spendId`) or system-stream (`chainId`), `protocolVersion` SHOULD be non-decreasing over time; downgrades SHOULD be rejected as `VersionMismatch` to avoid ambiguous semantics.

See ../../governance/versioning.md for upgrade semantics.
