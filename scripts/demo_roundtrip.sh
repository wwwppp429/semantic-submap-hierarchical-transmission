#!/usr/bin/env bash
set -e

NPZ="${1:-results/scan0000/scannet_mesh_scene0000_00_vox5cm_layers_robot.npz}"
OUTDIR="${2:-trace}"
ROBOT="${3:-0}"

TRACE="${OUTDIR}/scene_trace_r${ROBOT}.jsonl"

echo "[1/4] export trace..."
python3 scripts/export_trace.py \
  --npz "${NPZ}" \
  --out "${TRACE}" \
  --robot "${ROBOT}" \
  --max_packets 120 \
  --packet_voxels 256

echo "[2/4] validate json + crc..."
python3 scripts/validate_json.py "${TRACE}"

echo "[3/4] merge (original order) ..."
python3 scripts/merge_demo.py "${TRACE}" --out_json "${OUTDIR}/merge_summary_r${ROBOT}.json"

echo "[4/4] check order-independence ..."
python3 scripts/check_order_independence.py "${TRACE}" --trials 50

echo "[DONE] all checks passed."
