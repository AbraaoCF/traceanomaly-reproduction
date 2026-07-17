#!/usr/bin/env bash
# Idempotent setup for reproducing TraceAnomaly (ISSRE'20) on the TrainTicket testbed.
# Clones the upstream artifact, unpacks the released testbed data, and builds the
# pinned Docker image. Safe to re-run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="$ROOT/upstream"
UPSTREAM_REPO="https://github.com/NetManAIOps/TraceAnomaly.git"
DATA_DIR="$ROOT/data"
IMAGE="traceanomaly-repro:tf115"

echo "==> [1/3] Clone upstream artifact"
if [ ! -d "$UPSTREAM_DIR/.git" ]; then
  git clone --depth 1 "$UPSTREAM_REPO" "$UPSTREAM_DIR"
else
  echo "    already cloned: $UPSTREAM_DIR"
fi

echo "==> [2/3] Unpack released TrainTicket testbed data"
mkdir -p "$DATA_DIR"
for name in train test_normal test_abnormal; do
  if [ ! -f "$DATA_DIR/$name" ]; then
    unzip -o "$UPSTREAM_DIR/train_ticket/${name}.zip" -d "$DATA_DIR" >/dev/null
    echo "    unpacked $name ($(wc -l < "$DATA_DIR/$name") traces)"
  else
    echo "    already present: $DATA_DIR/$name"
  fi
done

echo "==> [3/3] Build pinned Docker image ($IMAGE)"
docker build -t "$IMAGE" -f "$ROOT/docker/Dockerfile" "$ROOT"

echo "==> Done. Next: scripts/run-experiment.sh"
