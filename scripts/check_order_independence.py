#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_order_independence.py

Run multiple shuffle trials and verify final merged state hash is identical.

Run:
  python3 scripts/check_order_independence.py trace/scene0000_00_r0.jsonl --trials 50
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from merge_demo import merge_trace, state_hash  # reuse logic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", help="trace.jsonl")
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    path = Path(args.trace)
    packets: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            packets.append(json.loads(line))

    rng = np.random.RandomState(args.seed)

    # Reference (original order)
    logodds0, sem0 = merge_trace(packets)
    href = state_hash(logodds0, sem0)

    ok = True
    for t in range(args.trials):
        pk = list(packets)
        rng.shuffle(pk)
        lo, se = merge_trace(pk)
        h = state_hash(lo, se)
        if h != href:
            print(f"[FAIL] trial={t} hash mismatch!")
            print(f"       ref={href}")
            print(f"       got={h}")
            ok = False
            break

    if ok:
        print(f"[OK] order-independence verified: trials={args.trials}, sha256={href}")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
