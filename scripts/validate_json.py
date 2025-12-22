#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validate_json.py
Validate packet JSON files:
- required fields
- payload schema (minimal)
- crc32 over canonical JSON without the 'crc32' field
"""

import argparse
import json
import os
import sys
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple


REQUIRED_TOP_KEYS = [
    "format_version", "submap_id", "robot_id", "layer",
    "version", "stamp", "payload", "crc32"
]


def canonical_bytes(pkt_wo_crc: Dict[str, Any]) -> bytes:
    s = json.dumps(pkt_wo_crc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def compute_crc32_hex(pkt: Dict[str, Any]) -> str:
    pkt2 = dict(pkt)
    pkt2.pop("crc32", None)
    c = zlib.crc32(canonical_bytes(pkt2)) & 0xFFFFFFFF
    return f"0x{c:08x}"


def validate_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "payload must be a dict"
    if "type" not in payload:
        return False, "payload.type missing"

    ptype = payload["type"]
    if ptype == "skeleton":
        # minimal check
        if "poses" not in payload or "factors" not in payload:
            return False, "skeleton payload must contain poses and factors"
        return True, "ok"

    if ptype == "occ_delta":
        ups = payload.get("updates", None)
        clamp = payload.get("clamp", None)
        if not isinstance(ups, list):
            return False, "occ_delta payload.updates must be a list"
        if clamp is None:
            return False, "occ_delta payload.clamp missing"
        # each update: [idx, delta_logodds, weight]
        for u in ups[:50]:  # don't over-check
            if not (isinstance(u, list) and len(u) == 3):
                return False, "occ_delta update must be [idx, delta, weight]"
            if not isinstance(u[0], int):
                return False, "occ_delta idx must be int"
        return True, "ok"

    if ptype == "sem_delta":
        ups = payload.get("updates", None)
        nc = payload.get("num_classes", None)
        if not isinstance(ups, list):
            return False, "sem_delta payload.updates must be a list"
        if not isinstance(nc, int) or nc <= 1:
            return False, "sem_delta payload.num_classes must be int > 1"
        # each update: [idx, label, weight]
        for u in ups[:50]:
            if not (isinstance(u, list) and len(u) == 3):
                return False, "sem_delta update must be [idx, label, weight]"
            if not isinstance(u[0], int) or not isinstance(u[1], int):
                return False, "sem_delta idx/label must be int"
        return True, "ok"

    return False, f"unknown payload.type={ptype}"


def iter_json_files(paths: List[str]) -> List[Path]:
    out: List[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            out += sorted([x for x in pp.rglob("*.json") if x.is_file()])
        else:
            out.append(pp)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="JSON files or directories")
    args = ap.parse_args()

    files = iter_json_files(args.inputs)
    if not files:
        print("[ERR] no json files found", file=sys.stderr)
        sys.exit(2)

    ok_all = True
    for fp in files:
        try:
            pkt = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            ok_all = False
            print(f"[FAIL] {fp}: cannot parse json: {e}")
            continue

        # top-level keys
        missing = [k for k in REQUIRED_TOP_KEYS if k not in pkt]
        if missing:
            ok_all = False
            print(f"[FAIL] {fp}: missing keys {missing}")
            continue

        # payload schema
        ok, msg = validate_payload(pkt["payload"])
        if not ok:
            ok_all = False
            print(f"[FAIL] {fp}: bad payload: {msg}")
            continue

        # crc
        crc_expect = str(pkt["crc32"]).lower()
        crc_got = compute_crc32_hex(pkt).lower()
        if crc_expect != crc_got:
            ok_all = False
            print(f"[FAIL] {fp}: crc mismatch expect={crc_expect} got={crc_got}")
            continue

        print(f"[OK]   {fp}")

    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
