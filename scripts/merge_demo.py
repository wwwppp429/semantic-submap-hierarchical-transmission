#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Merge packets in a trace using commutative/associative rules:

- L2: accumulate quantized log-odds deltas with exact integer addition (np.add.at),
      then apply ONE final clamp at the end.
- L3: per-voxel class histogram vote via np.add.at (commutative).

This design ensures order-independence under packet shuffling.
"""

import argparse
import base64
import json
import os
import zlib
from typing import Any, Dict, List, Tuple

import numpy as np


def b64z_unpack_ndarray(obj: Dict[str, Any]) -> np.ndarray:
    if obj.get("codec") != "b64z":
        raise ValueError("Unsupported codec (expected b64z)")
    dtype = np.dtype(obj["dtype"])
    shape = tuple(obj["shape"])
    raw = zlib.decompress(base64.b64decode(obj["data"].encode("ascii")))
    return np.frombuffer(raw, dtype=dtype).reshape(shape)


def load_trace(trace_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    header = None
    packets: List[Dict[str, Any]] = []
    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("type") == "header":
                header = obj
            elif obj.get("type") == "packet":
                packets.append(obj)
    if header is None:
        raise RuntimeError("Missing header in trace")
    return header, packets


def merge_packets(header: Dict[str, Any], packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_vox = int(header["n_vox"])
    lmax_q = int(header["lmax_q"])
    n_classes = int(header["n_classes"])

    # Raw accumulator (unclamped) -> order-independent
    Lq_raw = np.zeros(n_vox, dtype=np.int32)

    # Semantic vote counts
    sem_cnt = np.zeros((n_vox, n_classes), dtype=np.uint16)

    for pkt in packets:
        layer = int(pkt["layer"])
        payload = pkt["payload"]
        kind = payload.get("kind", "")

        if layer == 1:
            continue

        if kind == "L2_occ_delta":
            idx = b64z_unpack_ndarray(payload["indices"]).astype(np.int64)
            delta_q = b64z_unpack_ndarray(payload["delta_q"]).astype(np.int32)

            # IMPORTANT: use add.at to correctly handle repeated indices
            np.add.at(Lq_raw, idx, delta_q)

        elif kind == "L3_sem_delta":
            idx = b64z_unpack_ndarray(payload["indices"]).astype(np.int64)
            sem = b64z_unpack_ndarray(payload["sem"]).astype(np.int64)
            sem = np.clip(sem, 0, n_classes - 1)

            # IMPORTANT: use add.at for repeated (idx, sem) pairs
            np.add.at(sem_cnt, (idx, sem), 1)

        else:
            continue

    # ONE final clamp => commutative/associative overall
    Lq = np.clip(Lq_raw, -lmax_q, lmax_q).astype(np.int32)

    sem_label = sem_cnt.argmax(axis=1).astype(np.uint16)
    occ_bin = (Lq > 0).astype(np.uint8)

    return {"Lq": Lq, "sem_label": sem_label, "occ_bin": occ_bin}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--shuffle", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out_npz", default="out/merged_demo.npz")
    args = ap.parse_args()

    header, packets = load_trace(args.trace)

    if args.shuffle:
        rng = np.random.RandomState(args.seed)
        rng.shuffle(packets)

    out = merge_packets(header, packets)

    os.makedirs(os.path.dirname(args.out_npz), exist_ok=True)
    np.savez_compressed(
        args.out_npz,
        Lq=out["Lq"],
        sem_label=out["sem_label"],
        occ_bin=out["occ_bin"],
        n_vox=int(header["n_vox"]),
        lmax_q=int(header["lmax_q"]),
        q_scale=int(header["q_scale"]),
        n_classes=int(header["n_classes"]),
    )

    print(f"[OK] merged -> {args.out_npz}")
    print(f"     occ_bin_mean={float(out['occ_bin'].mean()):.4f}, unique_sem={len(np.unique(out['sem_label']))}")


if __name__ == "__main__":
    main()
