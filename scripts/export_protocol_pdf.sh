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
  "protocol/core/evidence.md"
  "protocol/core/spend-event.md"
  "protocol/core/verification-state.md"
  "protocol/core/spend-attestation.md"
  "protocol/core/canonicalization.md"
  "protocol/core/signatures-and-hashes.md"
  "protocol/core/privacy-boundaries.md"
  "protocol/core/ingestion.md"
  "protocol/core/normalization.md"
  "protocol/core/soft-verification.md"
  "protocol/core/hard-verification.md"
  "protocol/core/correction-and-revocation.md"
  "protocol/core/attestation-issuance.md"
  "protocol/portability/spend-attestation-token.md"
  "protocol/portability/verifier-requirements.md"
  "protocol/portability/identity-exclusion.md"
  "protocol/portability/replay-and-auditability.md"
  "protocol/applications/conditions/condition.md"
  "protocol/applications/conditions/condition-evaluation.md"
  "protocol/applications/conditions/proof-of-match.md"
  "protocol/applications/conditions/campaign-commitment.md"
  "protocol/applications/economics/reward-commitment.md"
  "protocol/applications/economics/reward-layer.md"
  "protocol/applications/economics/policy-layer.md"
  "protocol/applications/economics/gmv-token.md"
  "protocol/applications/economics/distribution-token.md"
  "protocol/applications/economics/settlement-bindings.md"
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

RESOURCE_PATH=".:00-purpose:protocol/core:protocol/portability:protocol/applications:06-extensions:07-conformance:08-governance:diagrams:formal"

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
