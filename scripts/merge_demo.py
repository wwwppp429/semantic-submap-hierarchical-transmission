#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_demo.py

Merge packets in given order (or shuffled) using commutative/associative rules:
  - occ_logodds_delta: logodds[idx] += delta, then clamp
  - sem_hist_delta: sem_count[idx, class] += count

Outputs:
  - prints final state hash
  - optionally dumps a small summary json

Run:
  python3 scripts/merge_demo.py trace/scene0000_00_r0.jsonl --shuffle --seed 0
"""

import argparse
import base64
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


def _unpack_array(packed: Dict[str, Any]) -> np.ndarray:
    if "raw" in packed:
        return np.asarray(packed["raw"])
    if "zlib_b64" in packed:
        c = base64.b64decode(packed["zlib_b64"].encode("ascii"))
        b = zlib.decompress(c)
        dtype = np.dtype(packed["dtype"])
        n = int(packed["n"])
        return np.frombuffer(b, dtype=dtype, count=n)
    raise ValueError("unknown packed array format")


def state_hash(logodds: Dict[int, float], sem_counts: Dict[int, Dict[int, int]]) -> str:
    h = hashlib.sha256()
    # Occ
    for k in sorted(logodds.keys()):
        h.update(f"o:{k}:{logodds[k]:.6f}\n".encode("utf-8"))
    # Sem
    for vidx in sorted(sem_counts.keys()):
        inner = sem_counts[vidx]
        for c in sorted(inner.keys()):
            h.update(f"s:{vidx}:{c}:{inner[c]}\n".encode("utf-8"))
    return h.hexdigest()


def merge_trace(packets: List[Dict[str, Any]]) -> Tuple[Dict[int, float], Dict[int, Dict[int, int]]]:
    logodds: Dict[int, float] = {}
    sem_counts: Dict[int, Dict[int, int]] = {}

    for pkt in packets:
        payload = pkt["payload"]
        ptype = payload["type"]

        if ptype == "occ_logodds_delta":
            idx = _unpack_array(payload["indices"]).astype(np.int64)
            dlt = _unpack_array(payload["delta_logodds"]).astype(np.float32)
            clamp = payload.get("clamp", {"min": -10.0, "max": 10.0})
            mn = float(clamp.get("min", -10.0))
            mx = float(clamp.get("max", 10.0))
            for i, dv in zip(idx.tolist(), dlt.tolist()):
                v = float(logodds.get(int(i), 0.0) + float(dv))
                v = max(mn, min(mx, v))
                logodds[int(i)] = v

        elif ptype == "sem_hist_delta":
            idx = _unpack_array(payload["indices"]).astype(np.int64)
            cls = _unpack_array(payload["class_id"]).astype(np.int64)
            count = int(payload.get("count", 1))
            for i, c in zip(idx.tolist(), cls.tolist()):
                i = int(i)
                c = int(c)
                if i not in sem_counts:
                    sem_counts[i] = {}
                sem_counts[i][c] = int(sem_counts[i].get(c, 0) + count)

        else:
            raise ValueError(f"Unknown payload type: {ptype}")

    return logodds, sem_counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", help="trace.jsonl")
    ap.add_argument("--shuffle", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out_json", default="", help="Optional summary output path")
    args = ap.parse_args()

    path = Path(args.trace)
    packets: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            packets.append(json.loads(line))

    if args.shuffle:
        rng = np.random.RandomState(args.seed)
        rng.shuffle(packets)

    logodds, sem_counts = merge_trace(packets)
    h = state_hash(logodds, sem_counts)

    print(f"[OK] merged packets={len(packets)}")
    print(f"     occ_vox={len(logodds)}, sem_vox={len(sem_counts)}")
    print(f"     state_sha256={h}")

    if args.out_json:
        outp = Path(args.out_json)
        outp.parent.mkdir(parents=True, exist_ok=True)
        # small summary only
        summary = {
            "packets": len(packets),
            "occ_vox": len(logodds),
            "sem_vox": len(sem_counts),
            "state_sha256": h,
        }
        outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"[OK] wrote {outp}")


if __name__ == "__main__":
    main()
