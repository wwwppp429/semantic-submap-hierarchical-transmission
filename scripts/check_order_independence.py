#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
check_order_independence.py

Given a packet set, verify order-independence by:
- computing a reference hash under name order
- shuffling many times and checking the same hash
"""

import argparse
import random
from typing import List

from merge_demo import load_packets, fuse_packets, state_hash


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", help="packet json files/dirs")
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_vox", type=int, default=2000)
    ap.add_argument("--num_classes", type=int, default=10)
    args = ap.parse_args()

    pkts = load_packets(args.inputs)
    # reference: name order (load_packets already sorts in dir mode)
    occ0, sem0 = fuse_packets(pkts, args.n_vox, args.num_classes)
    h0 = state_hash(occ0, sem0)
    print("[REF]", h0)

    rnd = random.Random(args.seed)
    for t in range(args.trials):
        pkts2 = list(pkts)
        rnd.shuffle(pkts2)
        occ, sem = fuse_packets(pkts2, args.n_vox, args.num_classes)
        h = state_hash(occ, sem)
        if h != h0:
            print(f"[FAIL] trial={t} hash={h} != ref")
            raise SystemExit(1)
        if (t + 1) % 10 == 0:
            print(f"[OK]   {t+1}/{args.trials}")

    print("[PASS] order-independence holds for all trials.")


if __name__ == "__main__":
    main()

