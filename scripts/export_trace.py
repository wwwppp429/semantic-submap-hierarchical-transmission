#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a small dataset-free packet trace (JSONL) for protocol sanity checks.

Each line is one JSON object:
  - header: {type:"header", format_version, n_vox, lmax_q, q_scale, n_classes, crc}
  - packet: {type:"packet", submap_id, robot_id, layer, version, stamp, payload, crc}

CRC is computed over canonical JSON of the object WITHOUT the 'crc' field.
"""

import argparse
import base64
import json
import os
import time
import zlib
from typing import Any, Dict, List

import numpy as np


def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    # stable: sorted keys, no spaces
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def attach_crc(obj_wo_crc: Dict[str, Any]) -> Dict[str, Any]:
    b = canonical_json_bytes(obj_wo_crc)
    crc = zlib.crc32(b) & 0xFFFFFFFF
    out = dict(obj_wo_crc)
    out["crc"] = int(crc)
    return out


def b64z_pack_ndarray(arr: np.ndarray) -> Dict[str, Any]:
    arr = np.ascontiguousarray(arr)
    raw = arr.tobytes(order="C")
    comp = zlib.compress(raw, level=6)
    b64 = base64.b64encode(comp).decode("ascii")
    return {"codec": "b64z", "dtype": str(arr.dtype), "shape": list(arr.shape), "data": b64}


def make_header(n_vox: int, lmax_q: int, q_scale: int, n_classes: int) -> Dict[str, Any]:
    hdr = {
        "type": "header",
        "format_version": "0.1.0",
        "n_vox": int(n_vox),
        "lmax_q": int(lmax_q),
        "q_scale": int(q_scale),
        "n_classes": int(n_classes),
        "note": "Dataset-free demo trace for prefix-decodable / order-independent fusion checks.",
    }
    return attach_crc(hdr)


def make_packet(
    submap_id: int,
    robot_id: int,
    layer: int,
    version: int,
    stamp: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    pkt = {
        "type": "packet",
        "submap_id": int(submap_id),
        "robot_id": int(robot_id),
        "layer": int(layer),      # 1=L1, 2=L2, 3=L3
        "version": int(version),  # monotonic-ish
        "stamp": int(stamp),
        "payload": payload,
    }
    return attach_crc(pkt)


def generate_synth_trace(
    n_vox: int,
    n_packets: int,
    seed: int,
    q_scale: int,
    lmax_float: float,
    n_classes: int,
) -> List[Dict[str, Any]]:
    rng = np.random.RandomState(seed)
    lmax_q = int(round(lmax_float * q_scale))

    trace: List[Dict[str, Any]] = []
    trace.append(make_header(n_vox=n_vox, lmax_q=lmax_q, q_scale=q_scale, n_classes=n_classes))

    version = 0
    stamp0 = int(time.time() * 1000)

    hot = rng.choice(n_vox, size=max(200, n_vox // 50), replace=False)

    for t in range(n_packets):
        version += 1
        stamp = stamp0 + t

        robot_id = int(rng.randint(0, 2))
        submap_id = int(rng.randint(0, 4))

        # occasionally emit L1 skeleton/meta
        if t % 20 == 0:
            payload = {"kind": "L1_skeleton", "text": f"demo backbone update v{version}"}
            trace.append(make_packet(submap_id, robot_id, 1, version, stamp, payload))
            continue

        layer = 2 if (t % 3 != 0) else 3

        n_upd = int(rng.randint(80, 200))
        idx_hot = rng.choice(hot, size=n_upd // 2, replace=True)
        idx_rnd = rng.randint(0, n_vox, size=n_upd - idx_hot.size)
        idx = np.concatenate([idx_hot, idx_rnd]).astype(np.int32)

        if layer == 2:
            # integer quantized log-odds delta => exact commutative merge
            hit = rng.rand(idx.size) < 0.7
            delta = np.where(hit, rng.randint(30, 120, size=idx.size), -rng.randint(5, 30, size=idx.size))
            delta_q = np.clip(delta, -32768, 32767).astype(np.int16)

            payload = {
                "kind": "L2_occ_delta",
                "indices": b64z_pack_ndarray(idx),
                "delta_q": b64z_pack_ndarray(delta_q),
            }
            trace.append(make_packet(submap_id, robot_id, 2, version, stamp, payload))
        else:
            cls = rng.randint(0, n_classes, size=idx.size).astype(np.uint16)
            payload = {
                "kind": "L3_sem_delta",
                "indices": b64z_pack_ndarray(idx),
                "sem": b64z_pack_ndarray(cls),
            }
            trace.append(make_packet(submap_id, robot_id, 3, version, stamp, payload))

    return trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="trace/trace_demo.jsonl")
    ap.add_argument("--n_vox", type=int, default=20000)
    ap.add_argument("--n_packets", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--q_scale", type=int, default=100)
    ap.add_argument("--lmax", type=float, default=6.0)
    ap.add_argument("--n_classes", type=int, default=20)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    trace = generate_synth_trace(
        n_vox=args.n_vox,
        n_packets=args.n_packets,
        seed=args.seed,
        q_scale=args.q_scale,
        lmax_float=args.lmax,
        n_classes=args.n_classes,
    )

    with open(args.out, "w", encoding="utf-8") as f:
        for obj in trace:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"[OK] wrote {len(trace)} lines -> {args.out}")


if __name__ == "__main__":
    main()
