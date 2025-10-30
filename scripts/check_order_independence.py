#!/usr/bin/env python3
"""
check_order_independence.py

Very small demo to show that SSPT messages (L1/L2/L3) can be applied
in arbitrary order and still result in a consistent submap state.

Expected repo layout:
  examples/
    l1_skeleton_example.json
    l2_delta_example.json
    l3_delta_example.json
"""

import json
from pathlib import Path
import random


# ---- tiny "central-side" state ----
# state = {
#   submap_id: {
#       "l1": {...} or None,
#       "l2": [ {...}, ... ],   # we just keep all deltas
#       "l3": [ {...}, ... ]
#   }
# }
def apply_msg(state, msg):
    layer = msg.get("layer") or msg.get("layer_id")
    # in examples you used string "L1"/"L2"/"L3"
    if isinstance(layer, str):
        layer = layer.upper()
    submap_id = None

    # 1) try transport-level header
    if "submap_id" in msg:
        submap_id = msg["submap_id"]
        payload = msg.get("payload", {})
    else:
        # 2) payload-only example, we fake an id
        submap_id = "example_submap"
        payload = msg

    sub_state = state.setdefault(submap_id, {"l1": None, "l2": [], "l3": []})

    if layer in (1, "L1"):
        sub_state["l1"] = payload
    elif layer in (2, "L2"):
        sub_state["l2"].append(payload)
    elif layer in (3, "L3"):
        sub_state["l3"].append(payload)
    else:
        print(f"[warn] unknown layer: {layer}")


def main():
    base = Path(__file__).resolve().parents[1] / "examples"
    candidates = [
        base / "l1_skeleton_example.json",
        base / "l2_delta_example.json",
        base / "l3_delta_example.json",
    ]
    # load all
    msgs = [json.loads(p.read_text()) for p in candidates]

    # shuffle to simulate out-of-order arrival
    random.shuffle(msgs)

    state = {}
    for m in msgs:
        apply_msg(state, m)

    # pretty-print final state
    print(json.dumps(state, indent=2))
    print("\n[ok] applied in order:", [m.get("layer") for m in msgs])


if __name__ == "__main__":
    main()
