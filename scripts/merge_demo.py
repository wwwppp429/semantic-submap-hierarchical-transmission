#!/usr/bin/env python3
import json
from pathlib import Path

def apply_msg(state, msg):
    layer = msg["layer"]
    submap_id = msg["submap_id"]
    s = state.setdefault(submap_id, {"l1": None, "l2": [], "l3": []})
    if layer == 1:
        s["l1"] = msg["payload"]
    elif layer == 2:
        s["l2"].append(msg["payload"])
    elif layer == 3:
        s["l3"].append(msg["payload"])

def main():
    state = {}
    base = Path("examples")
    for name in ["l1_skeleton.json", "l3_semantics_delta.json", "l2_geometry_delta.json"]:
        msg = json.loads((base / name).read_text())
        apply_msg(state, msg)
    print(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()
