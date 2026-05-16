# Crinkl Protocol V1

Canonical entrypoint for version 1 of the Crinkl Protocol specification. Each section below is normative unless explicitly marked non-normative.

- [GLOSSARY.md](./GLOSSARY.md) — normative term definitions
- [INTRODUCTION.md](./INTRODUCTION.md) — protocol overview and scope
- [MODEL.md](./MODEL.md) — core protocol concepts (spend-centric objects, scoped recipients, and ledgers)
- [TOKENS.md](./TOKENS.md) — token outputs (attestation + commitments)
- [DATA_STRUCTURES.md](./DATA_STRUCTURES.md) — canonical schema definitions
- [VERIFICATION_PIPELINE.md](./VERIFICATION_PIPELINE.md) — soft and hard verification flows
- [STATE_MACHINES.md](./STATE_MACHINES.md) — attestation and reward lifecycle transitions
- [EVENTS.md](./EVENTS.md) — event schemas and ordering requirements
- [REWARD_LAYER.md](./REWARD_LAYER.md) — application-layer reward interface (non-protocol)
- [ZK_LAYER.md](./ZK_LAYER.md) — optional zero-knowledge extension layer
- [ZK_FOUNDATION.md](./ZK_FOUNDATION.md) — minimum viable promo flow (ZK spine)
- [ZK_CIRCUIT_CATALOG.md](./ZK_CIRCUIT_CATALOG.md) — mapping from statement types to proof circuits (optional extension)
- [CAMPAIGN_SPEND_PROOF_PRIMITIVES.md](./CAMPAIGN_SPEND_PROOF_PRIMITIVES.md) — campaign rule composition from finite spend proof primitives (optional extension)
- [PROMO_PROTOCOL.md](./PROMO_PROTOCOL.md) — offer delivery profile + verifier rules (optional extension)
- [ENCRYPTION_ENVELOPES.md](./ENCRYPTION_ENVELOPES.md) — encrypted envelope formats for wallet/brand messages (optional extension)
- [TOKEN_EXTENSIONS.md](./TOKEN_EXTENSIONS.md) — privacy-first credentials + agent delegation (optional extension)
- [SECURITY_MODEL.md](./SECURITY_MODEL.md) — protocol security properties and invariants
- [PROTOCOL_EVOLUTION.md](./PROTOCOL_EVOLUTION.md) — governance and upgrade processes (placeholder)

## Protocol Requirements

**Integrity:** All events MUST include `eventHash` (SHA-256) and `prevHash` (linking to prior event in stream). Events MUST be signed with Ed25519.

**Identity boundary:** Internal spend-stream events MAY be wallet-scoped for issuer replay, routing, abuse controls, and reward handling. Portable Spend Attestation Tokens are separate derived artifacts and SHOULD omit wallet, user, account, and session identifiers for external verification unless recipient binding is explicitly required.

**Serialization:** Canonical JSON per RFC 8785 is REQUIRED. Alternative encodings (e.g., deterministic protobuf) MUST produce byte-identical hashes.
