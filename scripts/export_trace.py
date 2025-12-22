#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_trace.py

Export a small "packet trace" (JSONL) from a ScanNet layered NPZ.
- Input: scannet_mesh_sceneXXXX_YY_vox5cm_layers_robot.npz (must contain occ_L3, sem, robot_id)
- Output: trace.jsonl (one packet per line)
Packets are designed to be:
  - stateless
  - idempotent
  - commutative/associative under merge_demo.py rules

Payload types:
  - "occ_logodds_delta": indices + delta_logodds
  - "sem_hist_delta": indices + class_id (+count=1 implicitly)

Run:
  python3 scripts/export_trace.py \
    --npz results/scan0000/scannet_mesh_scene0000_00_vox5cm_layers_robot.npz \
    --out trace/scene0000_00_r0.jsonl \
    --robot 0 --max_packets 120 --packet_voxels 256
"""

import argparse
import base64
import json
import math
import os
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


def _canon_dumps(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def crc32_packet(pkt_wo_crc: Dict[str, Any]) -> int:
    return zlib.crc32(_canon_dumps(pkt_wo_crc)) & 0xFFFFFFFF


def chunk_indices(idxs: np.ndarray, chunk_size: int) -> List[np.ndarray]:
    return [idxs[i:i + chunk_size] for i in range(0, idxs.size, chunk_size)]


def build_center_weights(occ_shape: Tuple[int, int, int], idx_all: np.ndarray) -> np.ndarray:
    """Simple center-priority weight (deterministic)."""
    coords = np.vstack(np.unravel_index(idx_all, occ_shape)).T.astype(np.float32)
    center = coords.mean(axis=0)
    d = np.linalg.norm(coords - center, axis=1)
    d_max = float(d.max()) + 1e-6
    w = 1.0 + 2.5 * (1.0 - d / d_max) ** 2  # [1, ~3.5]
    return w.astype(np.float32)


def split_L1_L2(idx_sorted: np.ndarray, frac_L1: float) -> Tuple[np.ndarray, np.ndarray]:
    n = idx_sorted.size
    n1 = int(max(1, round(frac_L1 * n)))
    return idx_sorted[:n1], idx_sorted[n1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--robot", type=int, default=0, choices=[0, 1])
    ap.add_argument("--max_packets", type=int, default=120, help="Total packets across L1/L2/L3.")
    ap.add_argument("--packet_voxels", type=int, default=256, help="Max voxel updates per packet.")
    ap.add_argument("--frac_L1", type=float, default=0.15, help="Fraction of occupied voxels put into L1.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--compress", action="store_true", help="Compress payload arrays with zlib+base64 (optional).")
    args = ap.parse_args()

    npz_path = Path(args.npz)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = np.load(str(npz_path))
    for k in ["occ_L3", "sem", "robot_id"]:
        if k not in data:
            raise RuntimeError(f"NPZ missing key: {k}")

    occ = data["occ_L3"].astype(bool)
    sem = data["sem"].astype(np.int32)
    rid = data["robot_id"].astype(np.int32)

    occ_flat = occ.reshape(-1)
    sem_flat = sem.reshape(-1)
    rid_flat = rid.reshape(-1)

    mask = (occ_flat == 1) & (rid_flat == args.robot)
    idx_all = np.nonzero(mask)[0]
    if idx_all.size == 0:
        raise RuntimeError(f"No occupied voxels for robot={args.robot} in {npz_path.name}")

    # Deterministic ordering by center weight
    w = build_center_weights(occ.shape, idx_all)
    order = np.argsort(-w)  # high weight first
    idx_sorted = idx_all[order]

    idx_L1, idx_L2 = split_L1_L2(idx_sorted, args.frac_L1)
    idx_L3 = idx_all.copy()  # semantics for all occupied voxels (this robot region)

    # Downsample to keep trace small, but keep deterministic
    rng = np.random.RandomState(args.seed)
    # Budget packets roughly equally among L1/L2/L3 (at least 1 each)
    P = max(3, args.max_packets)
    p1 = max(1, int(round(P * 0.20)))
    p2 = max(1, int(round(P * 0.40)))
    p3 = max(1, P - p1 - p2)
    # Ensure >0
    if p3 <= 0:
        p3 = 1
        p2 = max(1, P - p1 - p3)

    # Cap voxels per layer so total packets won't explode
    def cap_to_packets(idxs: np.ndarray, n_packets: int) -> np.ndarray:
        max_vox = max(1, n_packets * args.packet_voxels)
        if idxs.size <= max_vox:
            return idxs
        # deterministic subsample: take evenly spaced indices
        take = np.linspace(0, idxs.size - 1, max_vox).astype(np.int64)
        return idxs[take]

    idx_L1 = cap_to_packets(idx_L1, p1)
    idx_L2 = cap_to_packets(idx_L2, p2)
    idx_L3 = cap_to_packets(idx_L3, p3)

    # Recompute actual chunking counts
    chunks_L1 = chunk_indices(idx_L1, args.packet_voxels)
    chunks_L2 = chunk_indices(idx_L2, args.packet_voxels)
    chunks_L3 = chunk_indices(idx_L3, args.packet_voxels)

    # Optionally compress arrays
    def pack_array_int(arr: np.ndarray) -> Dict[str, Any]:
        if not args.compress:
            return {"raw": arr.tolist()}
        b = np.asarray(arr, dtype=np.int32).tobytes()
        c = zlib.compress(b, level=6)
        return {"zlib_b64": base64.b64encode(c).decode("ascii"), "dtype": "int32", "n": int(arr.size)}

    def pack_array_f32(arr: np.ndarray) -> Dict[str, Any]:
        if not args.compress:
            return {"raw": [float(x) for x in arr.tolist()]}
        b = np.asarray(arr, dtype=np.float32).tobytes()
        c = zlib.compress(b, level=6)
        return {"zlib_b64": base64.b64encode(c).decode("ascii"), "dtype": "float32", "n": int(arr.size)}

    # Build packets
    scene_id = npz_path.stem.replace("scannet_mesh_", "").replace("_vox5cm_layers_robot", "")
    submap_id = f"{scene_id}_r{args.robot}"

    packets: List[Dict[str, Any]] = []
    stamp = 0

    # L1/L2 occ deltas: +1 logodds for included voxels
    for layer, chunks in [(1, chunks_L1), (2, chunks_L2)]:
        for ch in chunks:
            payload = {
                "type": "occ_logodds_delta",
                "indices": pack_array_int(ch),
                "delta_logodds": pack_array_f32(np.ones(ch.size, dtype=np.float32)),
                "clamp": {"min": -10.0, "max": 10.0},
            }
            pkt = {
                "schema": "sshx-trace-v1",
                "submap_id": submap_id,
                "robot_id": int(args.robot),
                "layer": int(layer),
                "version": 0,
                "stamp": int(stamp),
                "payload": payload,
            }
            pkt["crc32"] = crc32_packet(pkt)
            packets.append(pkt)
            stamp += 1

    # L3 semantics: histogram increment (count=1)
    for ch in chunks_L3:
        cls = sem_flat[ch].astype(np.int32)
        # ignore invalid (-1) just in case
        valid = cls >= 0
        ch2 = ch[valid]
        cls2 = cls[valid]
        payload = {
            "type": "sem_hist_delta",
            "indices": pack_array_int(ch2),
            "class_id": pack_array_int(cls2),
            "count": 1,
        }
        pkt = {
            "schema": "sshx-trace-v1",
            "submap_id": submap_id,
            "robot_id": int(args.robot),
            "layer": 3,
            "version": 0,
            "stamp": int(stamp),
            "payload": payload,
        }
        pkt["crc32"] = crc32_packet(pkt)
        packets.append(pkt)
        stamp += 1

    # Keep only first max_packets deterministically (still includes all layers)
    if len(packets) > args.max_packets:
        packets = packets[: args.max_packets]

    with out_path.open("w", encoding="utf-8") as f:
        for pkt in packets:
            f.write(json.dumps(pkt, ensure_ascii=False) + "\n")

    print(f"[OK] wrote {len(packets)} packets -> {out_path}")
    print(f"     submap_id={submap_id}, layers: "
          f"L1={sum(p['layer']==1 for p in packets)}, "
          f"L2={sum(p['layer']==2 for p in packets)}, "
          f"L3={sum(p['layer']==3 for p in packets)}")


if __name__ == "__main__":
    main()
