#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validate a JSONL trace:
- each line is valid JSON
- required keys exist
- crc matches canonical JSON of the object without 'crc'
"""

import argparse
import json
import zlib
from typing import Any, Dict


def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", help="trace JSONL path")
    args = ap.parse_args()

    n = 0
    ok = 0
    with open(args.trace, "r", encoding="utf-8") as f:
        for line in f:
            n += 1
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            if "crc" not in obj:
                raise RuntimeError(f"Line {n}: missing 'crc'")

            crc = int(obj["crc"])
            obj2 = dict(obj)
            obj2.pop("crc", None)
            crc2 = zlib.crc32(canonical_json_bytes(obj2)) & 0xFFFFFFFF
            if crc != crc2:
                raise RuntimeError(f"Line {n}: CRC mismatch: got {crc}, expect {crc2}")

            t = obj.get("type")
            if t == "header":
                for k in ["format_version", "n_vox", "lmax_q", "q_scale", "n_classes"]:
                    if k not in obj:
                        raise RuntimeError(f"Line {n}: header missing key '{k}'")
            elif t == "packet":
                for k in ["submap_id", "robot_id", "layer", "version", "stamp", "payload"]:
                    if k not in obj:
                        raise RuntimeError(f"Line {n}: packet missing key '{k}'")
            else:
                raise RuntimeError(f"Line {n}: unknown type '{t}'")

            ok += 1

    print(f"[OK] validated {ok}/{n} lines: {args.trace}")


if __name__ == "__main__":
    main()
