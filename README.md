# Semantic Submap Hierarchical Transmission (SSHT) — Layered & Prefix-Decodable Spec

This repository defines the L1/L2/L3 layered encoding for progressive, prefix-decodable transmission of semantic submaps in centralized multi-robot mapping. It implements the layered model described in Table I of our manuscript.

**Paper / Preprint:** (add link here)
**Repository:** (this page)

## Figures

<p align="center">
  <img src="diagrams/zt.png" width="95%">
</p>

<p align="center">
  <img src="diagrams/L1.png" width="32%">
  <img src="diagrams/L2.png" width="32%">
  <img src="diagrams/L3.png" width="32%">
</p>

<p align="center">
  <img src="diagrams/q1.png" width="48%">
  <img src="diagrams/q2.png" width="48%">
</p>



> We extend the classic progressive (layered + incremental) transmission paradigm to **3D voxel + semantics** and make it compatible with **robust PGO** and **octree occupancy fusion**.

| Layer | Purpose | Minimal payload (MUST) | Optional (SHOULD/MAY) |
|---|---|---|---|
| **L1 — Skeleton** | Make a consistent global frame fast | Submap poses; graph edges (odometry/loop closures) with info; time/version | Sparse geometry preview; calibration digest |
| **L2 — Geometry Δ** | Coarse geometry for planning/coverage | Octree block IDs; voxel occupancy ΔL; block resolution | Colors/normals; timestamps; view angles |
| **L3 — Semantics Δ** | High-res + semantics | Per-voxel class distribution (logits/probabilities) Δ; instance IDs/merge hints; attributes | Relations (scene graph edges); uncertainty stats |

**Prefix-decodable:** Applying `L1 → (L2 Δ)* → (L3 Δ)*` yields a valid map at any prefix.








## Files
- `specs/` — human-readable normative specs (MUST/SHOULD/MAY).
- `schemas/` — JSON Schemas for payload validation.
- `proto/` — Protobuf messages for wire format.
- `ros_msgs/` — ROS msg stubs (optional).
- `examples/` — Minimal valid payload examples.
- `diagrams/` — Figures for papers.
- `scripts/` — Utilities (validation).
- `examples/*_example.json` are **payload-only** examples (what the layer actually contains).
- `examples/*_msg.json` are **transport-level** messages with the common SSPT header
  (submap_id, robot_id, layer, version, stamp, payload, crc).
## Quick demo
To verify that SSHT messages can be applied **out of order** and still build a
consistent submap state, run the following command to verify order-independence and prefix-decodability:
```bash
python scripts/check_order_independence.py


## License
MIT. See `LICENSE`.

## Citation
See `CITATION.cff`.
