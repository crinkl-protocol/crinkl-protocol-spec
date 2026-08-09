# Released schema identifier collision erratum (v1)

This source-candidate erratum records the 22 released schema identifier
collisions without changing immutable released bytes, tags, runtime, or
deployment. See the [machine-readable erratum](released-schema-identifier-collisions-v1.json).

The corrected D4 effective receipt is
`sha256:d2441f0da9fef029fc8f59b099458c3e7ff22ffd181c3ee3f9fd75525113ccf9`.
It covers 22 mappings: 21 NATS binding schemas and one store schema. Each
mapping preserves the old released identities and names a D3.1 reviewed-source
successor from `crinkl-protocol` commit
`4ae7261c4b29de046ce268a3be126b92683579ec` by exact identifier, path, and
digest. Strict resolution uses release/tag+digest and fails ambiguity.

The successor map is reviewed source only: it is not adopted on `main`, public,
released, runtime, or deployed. Consumer migration is explicit and inactive;
identifier-only resolution was already unsafe where the old bytes differ; this
candidate does not create that condition.

Verification note: the local gate authenticates the historical release/tag and
digest evidence from this repository's released tags/full Git objects; it does
not claim shallow checkouts are sufficient.
