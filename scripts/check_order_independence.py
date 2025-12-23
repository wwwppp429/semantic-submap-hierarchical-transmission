#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Order-independence test for the trace merge.

Runs merge in original order and in multiple random shuffled orders.
Asserts outputs are exactly identical (L2 integer log-odds + L3 histogram vote).
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

# Ensure scripts/ is importable when run from repo root.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from merge_demo import load_trace, merge_packets  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--n_shuffles", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    header, packets = load_trace(args.trace)

    ref = merge_packets(header, packets)
    ref_Lq = ref["Lq"].copy()
    ref_sem = ref["sem_label"].copy()
    ref_occ = ref["occ_bin"].copy()

    rng = np.random.RandomState(args.seed)
    for i in range(args.n_shuffles):
        pk = list(packets)
        rng.shuffle(pk)
        out = merge_packets(header, pk)

        if not np.array_equal(out["Lq"], ref_Lq):
            raise RuntimeError(f"Mismatch in Lq at shuffle {i}")
        if not np.array_equal(out["sem_label"], ref_sem):
            raise RuntimeError(f"Mismatch in sem_label at shuffle {i}")
        if not np.array_equal(out["occ_bin"], ref_occ):
            raise RuntimeError(f"Mismatch in occ_bin at shuffle {i}")

    print(f"[OK] order-independence verified with {args.n_shuffles} shuffles.")


if __name__ == "__main__":
    main()
