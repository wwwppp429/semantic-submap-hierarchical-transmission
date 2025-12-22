#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKT_DIR="${ROOT_DIR}/demo_packets"

echo "[1/4] generate demo packets..."
python3 "${ROOT_DIR}/scripts/merge_demo.py" \
  --make_demo \
  --out_dir "${PKT_DIR}" \
  --seed 0 \
  --n_vox 2000 \
  --num_classes 10 \
  --n_submaps 4 \
  --n_per_layer 200

echo "[2/4] validate json + crc..."
python3 "${ROOT_DIR}/scripts/validate_json.py" "${PKT_DIR}"

echo "[3/4] merge in name order (reference hash)..."
python3 "${ROOT_DIR}/scripts/merge_demo.py" \
  --inputs "${PKT_DIR}" \
  --order name \
  --n_vox 2000 \
  --num_classes 10

echo "[4/4] check order-independence..."
# ensure scripts/ is on PYTHONPATH for the import
PYTHONPATH="${ROOT_DIR}/scripts:${PYTHONPATH}" \
python3 "${ROOT_DIR}/scripts/check_order_independence.py" \
  --inputs "${PKT_DIR}" \
  --trials 50 \
  --seed 0 \
  --n_vox 2000 \
  --num_classes 10

echo "[DONE] all checks passed."

