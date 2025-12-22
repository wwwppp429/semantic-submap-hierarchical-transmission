#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_demo.py

Two uses:
1) --make_demo: generate toy packets under the repo's packet schema.
2) Merge packets in a given order and output a deterministic hash of the final fused state.

Fusion rules:
- occ_delta: log-odds additive + clamp
- sem_delta: weighted count accumulation
These are commutative/associative (order-independent).
"""

import argparse
import hashlib
import json
import random
import time
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


def canonical_bytes(pkt_wo_crc: Dict[str, Any]) -> bytes:
    s = json.dumps(pkt_wo_crc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def add_crc32(pkt: Dict[str, Any]) -> Dict[str, Any]:
    pkt2 = dict(pkt)
    pkt2.pop("crc32", None)
    c = zlib.crc32(canonical_bytes(pkt2)) & 0xFFFFFFFF
    pkt["crc32"] = f"0x{c:08x}"
    return pkt


def load_packets(inputs: List[str]) -> List[Dict[str, Any]]:
    files: List[Path] = []
    for p in inputs:
        pp = Path(p)
        if pp.is_dir():
            files += sorted([x for x in pp.rglob("*.json") if x.is_file()])
        else:
            files.append(pp)
    pkts = []
    for fp in files:
        pkts.append(json.loads(fp.read_text(encoding="utf-8")))
    return pkts


def fuse_packets(pkts: List[Dict[str, Any]], n_vox: int, num_classes: int) -> Tuple[np.ndarray, np.ndarray]:
    occ = np.zeros((n_vox,), dtype=np.float32)                # log-odds
    sem = np.zeros((n_vox, num_classes), dtype=np.float32)    # counts

    for pkt in pkts:
        p = pkt["payload"]
        if p["type"] == "occ_delta":
            clamp = float(p["clamp"])
            for idx, dlog, w in p["updates"]:
                occ[idx] = np.clip(occ[idx] + float(dlog) * float(w), -clamp, clamp)

        elif p["type"] == "sem_delta":
            for idx, lab, w in p["updates"]:
                if 0 <= lab < num_classes:
                    sem[idx, lab] += float(w)

        elif p["type"] == "skeleton":
            # demo only: no-op
            pass

    return occ, sem


def state_hash(occ: np.ndarray, sem: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(occ.tobytes())
    h.update(sem.tobytes())
    return h.hexdigest()


def make_demo(out_dir: Path, seed: int, n_vox: int, num_classes: int,
              n_submaps: int, n_per_layer: int) -> None:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    fmt = "0.1.1"
    stamp0 = int(time.time())

    # make L1/L2/L3 packets for each submap
    pid = 0
    for sm in range(n_submaps):
        for ver in range(1, 2):  # keep simple
            # L1 skeleton
            pkt = {
                "format_version": fmt,
                "submap_id": f"submap_{sm}",
                "robot_id": sm % 2,
                "layer": "L1",
                "version": ver,
                "stamp": stamp0 + pid,
                "payload": {
                    "type": "skeleton",
                    "poses": [{"id": 0, "t": [0, 0, 0]}],
                    "factors": [{"type": "odom", "i": 0, "j": 1}],
                },
            }
            add_crc32(pkt)
            (out_dir / f"{pid:03d}_L1_submap{sm}.json").write_text(json.dumps(pkt, indent=2), encoding="utf-8")
            pid += 1

            # L2 occ_delta
            ups = []
            for _ in range(n_per_layer):
                idx = rng.randrange(0, n_vox)
                dlog = rng.uniform(-1.0, 1.0)
                w = rng.uniform(0.5, 2.0)
                ups.append([idx, dlog, w])
            pkt = {
                "format_version": fmt,
                "submap_id": f"submap_{sm}",
                "robot_id": sm % 2,
                "layer": "L2",
                "version": ver,
                "stamp": stamp0 + pid,
                "payload": {
                    "type": "occ_delta",
                    "clamp": 4.0,
                    "updates": ups,
                },
            }
            add_crc32(pkt)
            (out_dir / f"{pid:03d}_L2_submap{sm}.json").write_text(json.dumps(pkt, indent=2), encoding="utf-8")
            pid += 1

            # L3 sem_delta
            ups = []
            for _ in range(n_per_layer):
                idx = rng.randrange(0, n_vox)
                lab = rng.randrange(0, num_classes)
                w = rng.uniform(0.5, 2.0)
                ups.append([idx, lab, w])
            pkt = {
                "format_version": fmt,
                "submap_id": f"submap_{sm}",
                "robot_id": sm % 2,
                "layer": "L3",
                "version": ver,
                "stamp": stamp0 + pid,
                "payload": {
                    "type": "sem_delta",
                    "num_classes": num_classes,
                    "updates": ups,
                },
            }
            add_crc32(pkt)
            (out_dir / f"{pid:03d}_L3_submap{sm}.json").write_text(json.dumps(pkt, indent=2), encoding="utf-8")
            pid += 1

    print(f"[OK] demo packets written to {out_dir} (count={pid})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="*", default=[], help="packet json files/dirs")
    ap.add_argument("--order", choices=["name", "shuffle"], default="name")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_vox", type=int, default=2000)
    ap.add_argument("--num_classes", type=int, default=10)

    ap.add_argument("--make_demo", action="store_true", help="generate toy packets")
    ap.add_argument("--out_dir", default="demo_packets")
    ap.add_argument("--n_submaps", type=int, default=4)
    ap.add_argument("--n_per_layer", type=int, default=200)

    args = ap.parse_args()

    if args.make_demo:
        make_demo(Path(args.out_dir), args.seed, args.n_vox, args.num_classes, args.n_submaps, args.n_per_layer)
        return

    if not args.inputs:
        raise SystemExit("need --inputs <dir or json files>")

    pkts = load_packets(args.inputs)
    if args.order == "shuffle":
        rnd = random.Random(args.seed)
        rnd.shuffle(pkts)

    occ, sem = fuse_packets(pkts, args.n_vox, args.num_classes)
    print("[HASH]", state_hash(occ, sem))
    print("[STATS] occ_logodds: min=%.3f max=%.3f" % (float(occ.min()), float(occ.max())))
    print("[STATS] sem_counts:  sum=%.3f" % float(sem.sum()))


if __name__ == "__main__":
    main()

