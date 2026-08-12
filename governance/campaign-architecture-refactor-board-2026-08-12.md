---
status: complete
layer: governance
version: v1
normative: false
---

# Campaign architecture refactor atomic board — 2026-08-12

Plan anchor: [`campaign-architecture-refactor-plan-2026-08-12.md`](campaign-architecture-refactor-plan-2026-08-12.md)

| ID | Atomic step | Status | Evidence |
|---|---|---|---|
| CA-01 | Read governing instructions and pin exact source commits | complete | plan baseline |
| CA-02 | Inventory objects, schemas, producers, consumers, hashes, signatures, certificates, and cross-references | complete | migration inventory |
| CA-03 | Record the collision table and select one canonical term per mechanism | complete | evidence document |
| CA-04 | Establish canonical architecture, glossary, authority matrix, producer/consumer matrix, lifecycle, and economic-admission boundary | complete | Campaign architecture document |
| CA-05 | Add first canonical Campaign V1 schemas | complete | campaign schema directory |
| CA-06 | Refactor old Campaign commitment and ProofOfMatch pages | complete | conditions documents |
| CA-07 | Update settlement, admission, extension, glossary, index, and README references | complete | cumulative diff |
| CA-08 | Add Monster experiment, direct-promotion, and capacity-limited narratives | complete | conformance narrative |
| CA-09 | Add Boost mapping and current-versus-target matrix | complete | migration document |
| CA-10 | Add Proof Validator refactor handoff | complete | validator handoff document |
| CA-11 | Run schema, conformance, version, link, documentation, and stale-vocabulary checks | complete | validation receipt, including pre-existing inventory-gate failure |
| CA-12 | Review final diff and close the slice | complete | final scoped status/diff review and validation receipt |
| CA-13 | Remove unimplemented Campaign predecessor mappings, aliases, deprecation scaffolding, and inherited schema versions | complete | canonical V1 schemas, clean Campaign scan, protected Spend/pipeline diff, validation receipt |

At most one row is active. No row changes implementation, release, runtime,
validator authority, escrow funds, or production state.
