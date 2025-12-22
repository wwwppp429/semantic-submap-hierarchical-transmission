#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_json.py

Validate JSONL trace:
  - required fields
  - type/range checks
  - crc32 check (canonical json)

Run:
  python3 scripts/validate_json.py trace/scene0000_00_r0.jsonl
"""

import argparse
import base64
import json
import zlib
from pathlib import Path
from typing import Any, Dict


def _canon_dumps(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def crc32_packet(pkt_wo_crc: Dict[str, Any]) -> int:
    return zlib.crc32(_canon_dumps(pkt_wo_crc)) & 0xFFFFFFFF


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", help="trace.jsonl")
    args = ap.parse_args()

    path = Path(args.trace)
    n = 0
    bad = 0
    layers = {1: 0, 2: 0, 3: 0}

    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                pkt = json.loads(line)
            except Exception as e:
                print(f"[ERR] line {ln}: invalid JSON: {e}")
                bad += 1
                continue

            # Required top-level fields
            req = ["schema", "submap_id", "robot_id", "layer", "version", "stamp", "payload", "crc32"]
            for k in req:
                if k not in pkt:
                    print(f"[ERR] line {ln}: missing field '{k}'")
                    bad += 1
                    break
            else:
                # Type checks
                if pkt["schema"] != "sshx-trace-v1":
                    print(f"[ERR] line {ln}: schema mismatch: {pkt['schema']}")
                    bad += 1
                    continue
                if not isinstance(pkt["submap_id"], str):
                    print(f"[ERR] line {ln}: submap_id not str")
                    bad += 1
                    continue
                if pkt["robot_id"] not in [0, 1]:
                    print(f"[ERR] line {ln}: robot_id must be 0/1")
                    bad += 1
                    continue
                if pkt["layer"] not in [1, 2, 3]:
                    print(f"[ERR] line {ln}: layer must be 1/2/3")
                    bad += 1
                    continue
                if not isinstance(pkt["version"], int) or pkt["version"] < 0:
                    print(f"[ERR] line {ln}: version invalid")
                    bad += 1
                    continue
                if not isinstance(pkt["stamp"], int) or pkt["stamp"] < 0:
                    print(f"[ERR] line {ln}: stamp invalid")
                    bad += 1
                    continue
                if not isinstance(pkt["payload"], dict) or "type" not in pkt["payload"]:
                    print(f"[ERR] line {ln}: payload invalid")
                    bad += 1
                    continue
                if not isinstance(pkt["crc32"], int):
                    print(f"[ERR] line {ln}: crc32 invalid")
                    bad += 1
                    continue

                # CRC check
                pkt2 = dict(pkt)
                crc = pkt2.pop("crc32")
                crc_ref = crc32_packet(pkt2)
                if (crc & 0xFFFFFFFF) != crc_ref:
                    print(f"[ERR] line {ln}: crc mismatch got={crc} ref={crc_ref}")
                    bad += 1
                    continue

                layers[pkt["layer"]] += 1

    print(f"[OK] {n} packets checked, bad={bad}")
    print(f"     layers: L1={layers[1]}, L2={layers[2]}, L3={layers[3]}")
    if bad > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
