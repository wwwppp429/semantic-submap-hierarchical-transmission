# Semantic Submap Hierarchical Transmission (SSHT) — Layered & Prefix-Decodable Spec

This repository defines the L1/L2/L3 layered encoding for progressive, prefix-decodable transmission of semantic submaps in centralized multi-robot mapping. It implements the layered model described in Table I of our manuscript.

## Scope (Important)
This repository is **not** the full system code of the paper.
It is a lightweight companion repo that provides **figures + a concise L1/L2/L3 layered-submap specification**
to explain *why and how hierarchical (prefix-decodable) transmission is used* under bandwidth constraints.

- Full mapping system: implemented in C++ (not included here).
- This repo: figures, schemas/proto, examples, and small sanity-check scripts (optional).




**Paper / Preprint:** (add link here)
**Repository:** (this page)

## Figures

<p align="center">
  <a href="diagrams/zt.png">
    <img src="diagrams/zt.png" width="95%"/>
  </a>
</p>

<p align="center">
  <a href="diagrams/L1.png"><img src="diagrams/L1.png" width="32%"/></a>
  <a href="diagrams/L2.png"><img src="diagrams/L2.png" width="32%"/></a>
  <a href="diagrams/L3.png"><img src="diagrams/L3.png" width="32%"/></a>
</p>

<p align="center">
  <a href="diagrams/q1.png"><img src="diagrams/q1.png" width="48%"/></a>
  <a href="diagrams/q2.png"><img src="diagrams/q2.png" width="48%"/></a>
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
## Optional sanity check (toy example)
This toy script only checks prefix-decodability / order-independence of the message format,
and does **not** reproduce the full SLAM pipeline.

```bash
python scripts/check_order_independence.py


## License
MIT. See `LICENSE`.

## Citation
See `CITATION.cff`.
