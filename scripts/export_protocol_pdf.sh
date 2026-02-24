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
  "protocol/ABSTRACT.md"
  "protocol/INTRODUCTION.md"
  "protocol/GLOSSARY.md"
  "protocol/MODEL.md"
  "protocol/PROTOCOL_V1.md"
  "protocol/DATA_STRUCTURES.md"
  "protocol/EVENTS.md"
  "protocol/STATE_MACHINES.md"
  "protocol/VERIFICATION_PIPELINE.md"
  "protocol/REWARD_LAYER.md"
  "protocol/TOKENS_OVERVIEW.md"
  "protocol/TOKENS.md"
  "protocol/TOKEN_EXTENSIONS.md"
  "protocol/COMMITMENT_LAYER.md"
  "protocol/ZK_FOUNDATION.md"
  "protocol/ZK_LAYER.md"
  "protocol/SECURITY_MODEL.md"
  "protocol/RATE_LIMITING.md"
  "protocol/PROTOCOL_EVOLUTION.md"
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

RESOURCE_PATH=".:protocol:reference:diagrams:formal"

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
