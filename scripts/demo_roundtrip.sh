#!/usr/bin/env bash
set -euo pipefail

# Run from repo root
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

mkdir -p trace out

TRACE="trace/trace_demo.jsonl"

# 1) Generate a small trace (dataset-free)
python scripts/export_trace.py --out "${TRACE}" --n_packets 200 --seed 0

# 2) Validate JSON + CRC
python scripts/validate_json.py "${TRACE}"

# 3) Check order-independence (shuffle)
python scripts/check_order_independence.py --trace "${TRACE}" --n_shuffles 20 --seed 0

# 4) Merge once and export a tiny artifact
python scripts/merge_demo.py --trace "${TRACE}" --out_npz out/merged_demo.npz

echo "[OK] demo roundtrip finished."
