# Layered Submap Model (L1 / L2 / L3)

This document describes the *semantic meaning* of the three layers used
in our hierarchical transmission scheme. It is intentionally short and
matches the table in the paper.

---

## Overview

Each submap is represented as a stack of layers:

1. **L1 — Skeleton**
2. **L2 — Geometry Δ**
3. **L3 — Semantics Δ**

The key design goal is:

> Any prefix (L1, or L1+L2, or L1+L2+L3) yields a usable global map,
> and all increments can be fused in any order.

---

## L1 — Skeleton

**Purpose.**
Make the global frame usable as early as possible with minimal bytes.

**Content (MUST).**

- Submap pose(s) in the world frame.
- Odometry and loop-closure edges with information (covariance / weight).
- A monotonically increasing `version` per submap.

**Content (SHOULD / MAY).**

- Small calibration / meta-data (sensor intrinsics, extrinsics digest).
- Optional coarse “hull” occupancy preview for visualization.

**Notes.**

- L1 packets are small and sent even under very low bandwidth.
- All higher layers are interpreted relative to the pose provided by L1.

---

## L2 — Geometry Δ

**Purpose.**
Refine geometry and occupancy while keeping updates sparse.

**Content (MUST).**

- A set of voxel indices touched in this increment.
- Quantized log-odds increments `ΔL_q` for these voxels
  (e.g. `int16` in fixed-point units).
- Parameters `lmax_q`, `q_scale` (given in the header).

**Fusion rule.**

Let `Lq(n)` be the current quantized log-odds of voxel `n`. For each
update `(idx, ΔLq)` in the packet:

```text
Lq(idx) ← clip( Lq(idx) + ΔLq,  -lmax_q, +lmax_q )
```

This operation is **commutative and associative**, so packets may be
applied in any order.

**Content (SHOULD / MAY).**

* Voxel timestamps or view directions.
* Block-level aggregation (octree blocks, chunks) to save indices.

---

## L3 — Semantics Δ

**Purpose.**
Add semantic information and small-object details on top of geometry.

**Content (MUST).**

* Voxel indices touched by this increment.
* A class ID per index (`uint16`) or a short discrete distribution.

**Fusion rule.**

* Maintain per-voxel integer class counts `cnt(n, c)`.
* For each update `(idx, cls)`:

```text
cnt(idx, cls) ← cnt(idx, cls) + 1
label(idx)    ← argmax_c cnt(idx, c)
```

This is again **commutative and associative**.

**Content (SHOULD / MAY).**

* Instance IDs and merge hints to help downstream instance fusion.
* Uncertainty metrics or entropy estimates.

---

## Prefix-decodability

Given:

* L1 provides poses and basic connectivity,
* L2 refines occupancy, and
* L3 adds semantics,

we can always decode a consistent map from any prefix:

* **L1 only** → rough but globally consistent skeleton map.
* **L1 + L2** → geometrically usable occupancy map.
* **L1 + L2 + L3** → full metric-semantic map.

The demo scripts in `scripts/` implement exactly this model on a small
synthetic trace.
