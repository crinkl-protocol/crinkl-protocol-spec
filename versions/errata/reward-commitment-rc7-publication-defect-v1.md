# Reward-commitment rc.7 publication defect erratum (v1)

This additive erratum preserves immutable `v1.0.0-rc.7` history: tag
`v1.0.0-rc.7`, commit `d45560e679c12298ee25fad6e0e7948b03e5a7c5`, and tree
`9bbc61fc791ef6390cf0c0d07cb9d2b0b1329ec5`. It does not rewrite released
bytes, alter a released vector, activate runtime behavior, or grant authority.

For the named conflicts, released bytes cannot be reduced to one unambiguous
meaning. Consumers must resolve them through the tag, path, and exact digest
pins in the [machine-readable erratum](reward-commitment-rc7-publication-defect-v1.json),
not by a mutable branch or an identifier alone.

The erratum pins adopted candidate
`crinkl-protocol@093b37db3e78bdd4253d7864ae4eb5398ce7cc25` as candidate-source
evidence. A later `v1.0.0-rc.8` / suite-5 successor must preserve the legacy
vector and use a distinct successor identity. Publication, runtime consumption,
deployment, validator support, and authority activation remain separate and
unclaimed.
