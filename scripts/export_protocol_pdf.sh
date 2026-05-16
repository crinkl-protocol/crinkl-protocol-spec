#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"

OUT_REL="${1:-dist/crinkl-protocol.pdf}"
OUT_PATH="$ROOT_DIR/$OUT_REL"
OUT_DIR="$(dirname "$OUT_PATH")"

mkdir -p "$OUT_DIR"

TMP_MD="$(mktemp)"
cleanup() { rm -f "$TMP_MD"; }
trap cleanup EXIT

TITLE="Crinkl Protocol"
SUBTITLE="Normative specification"

cat >"$TMP_MD" <<EOF
---
title: "$TITLE"
subtitle: "$SUBTITLE"
---

EOF

DOCS=(
  "00-purpose/what-crinkl-proves.md"
  "00-purpose/non-goals.md"
  "00-purpose/threat-model.md"
  "01-core/evidence.md"
  "01-core/spend-event.md"
  "01-core/verification-state.md"
  "01-core/spend-attestation.md"
  "01-core/canonicalization.md"
  "01-core/signatures-and-hashes.md"
  "01-core/privacy-boundaries.md"
  "02-proof-lifecycle/ingestion.md"
  "02-proof-lifecycle/normalization.md"
  "02-proof-lifecycle/soft-verification.md"
  "02-proof-lifecycle/hard-verification.md"
  "02-proof-lifecycle/correction-and-revocation.md"
  "02-proof-lifecycle/attestation-issuance.md"
  "03-portability/spend-attestation-token.md"
  "03-portability/verifier-requirements.md"
  "03-portability/identity-exclusion.md"
  "03-portability/replay-and-auditability.md"
  "04-condition-layer/condition.md"
  "04-condition-layer/condition-evaluation.md"
  "04-condition-layer/proof-of-match.md"
  "04-condition-layer/campaign-commitment.md"
  "05-reward-and-settlement/reward-commitment.md"
  "05-reward-and-settlement/reward-layer.md"
  "05-reward-and-settlement/policy-layer.md"
  "05-reward-and-settlement/gmv-token.md"
  "05-reward-and-settlement/distribution-token.md"
  "05-reward-and-settlement/settlement-bindings.md"
  "06-extensions/zk-proof-extension.md"
  "06-extensions/zk-foundation.md"
  "06-extensions/zk-circuit-catalog.md"
  "06-extensions/agent-query-extension.md"
  "06-extensions/mcp-rest-bindings.md"
  "06-extensions/solana-commitment-binding.md"
  "06-extensions/offer-delivery-profile.md"
  "06-extensions/encryption-envelopes.md"
  "06-extensions/store-registry.md"
  "07-conformance/vectors.md"
  "07-conformance/verifier-test-suite.md"
  "07-conformance/compatibility.md"
  "08-governance/glossary.md"
  "08-governance/protocol-v1-index.md"
  "08-governance/versioning.md"
  "08-governance/change-process.md"
  "08-governance/authority-hierarchy.md"
)

for doc in "${DOCS[@]}"; do
  if [[ ! -f "$ROOT_DIR/$doc" ]]; then
    echo "Missing required file: $doc" >&2
    exit 1
  fi

  {
    echo
    echo "\\newpage"
    echo
    cat "$ROOT_DIR/$doc"
    echo
  } >>"$TMP_MD"
done

RESOURCE_PATH=".:00-purpose:01-core:02-proof-lifecycle:03-portability:04-condition-layer:05-reward-and-settlement:06-extensions:07-conformance:08-governance:diagrams:formal"

IMAGE="crinkl-protocol/pandoc-latex:latest"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker build -t "$IMAGE" -f "$ROOT_DIR/scripts/pandoc/Dockerfile" "$ROOT_DIR/scripts/pandoc" >/dev/null
fi

docker run --rm \
  -v "$ROOT_DIR:/data" \
  -v "$TMP_MD:/tmp/PROTOCOL_BOOK.md:ro" \
  -w /data \
  "$IMAGE" \
  /tmp/PROTOCOL_BOOK.md \
  --from=gfm \
  --toc \
  --number-sections \
  --pdf-engine=xelatex \
  -V mainfont="DejaVu Serif" \
  -V sansfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  --resource-path="$RESOURCE_PATH" \
  --syntax-highlighting=default \
  -o "$OUT_REL"

echo "Wrote $OUT_REL"
