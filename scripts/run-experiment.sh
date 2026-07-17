#!/usr/bin/env bash
# Run the TraceAnomaly reproduction on the TrainTicket testbed inside the pinned
# image, then reconstruct precision/recall (RQ1) and apply the KDE + p-value
# decision step (RQ2). Run scripts/bootstrap.sh first.
#
# Env overrides:
#   MAX_EPOCH (default 100)   TEST_N_Z (default 500)   ALPHA (default 0.001)
# NOTE 1: the upstream code sets no random seed, so numbers are close but not
# bit-identical across runs (expect the ranges in reference-results/AGGREGATE.md).
# NOTE 2: tfsnippet's early_stopping does NOT halt training -- it only restores
# the best-validation params at the end, and validation peaks within the first few
# dozen epochs. So MAX_EPOCH=100 (default, ~1h on CPU) yields a model equivalent to
# the released cap of 2000 epochs (which would take ~1.5 days for no extra benefit).
# Set MAX_EPOCH=2000 to run that literal cap.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="traceanomaly-repro:tf115"
DATA_DIR="$ROOT/data"
UPSTREAM_DIR="$ROOT/upstream"
RESULTS_DIR="$ROOT/results"
MAX_EPOCH="${MAX_EPOCH:-100}"
TEST_N_Z="${TEST_N_Z:-500}"
ALPHA="${ALPHA:-0.001}"
NAME="testbed"

mkdir -p "$RESULTS_DIR"

echo "==> Training + detection (max_epoch=$MAX_EPOCH, test_n_z=$TEST_N_Z)"
docker run --rm -i \
  -v "$UPSTREAM_DIR":/code -v "$DATA_DIR":/data:ro -v "$RESULTS_DIR":/results \
  -w /code "$IMAGE" bash -lc "
    python -m traceanomaly.main \
      --trainpath /data/train --normalpath /data/test_normal --abnormalpath /data/test_abnormal \
      --outputpath $NAME -c flow_type=rnvp -c max_epoch=$MAX_EPOCH -c test_n_z=$TEST_N_Z
    cp /code/webankdata/rnvp_${NAME}.csv /results/rnvp_${NAME}.csv
    cp /code/webankdata/vrnvp_${NAME}.csv /results/vrnvp_${NAME}.csv
  "

echo "==> Reconstructing metrics (RQ1) + KDE+p-value decision (RQ2)"
docker run --rm -i \
  -v "$ROOT/src":/src:ro -v "$RESULTS_DIR":/results \
  "$IMAGE" python /src/evaluate.py "/results/rnvp_${NAME}.csv" \
    --normal-scores "/results/vrnvp_${NAME}.csv" --alpha "$ALPHA" --plot "/results/pr_curve.png"

echo "==> Done. Scored traces + PR curve in $RESULTS_DIR/"
