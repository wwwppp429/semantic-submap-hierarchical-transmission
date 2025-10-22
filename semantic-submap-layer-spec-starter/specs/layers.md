# Layer Definitions (Normative)

This document uses RFC 2119 keywords (MUST, SHOULD, MAY).

## Common
- Each payload MUST include: `block_id`, `layer`, `version`, `frame_id`, `T_submap_world` (or a submap ID resolvable to that transform), and a monotonic `timestamp`.
- Blocks MUST be addressable in a **Block–Layer Prefix Model**: for each block `k`, layers `j∈{0,1,2,3}` where `0` means "not sent".
- A receiver MUST apply deltas in order of increasing layer and increasing version per block.

## L1 — Skeleton
- MUST contain: submap nodes `{id, pose, cov/info}`, edges `{(i,j), type∈{odom,loop}, info}`.
- SHOULD contain: calibration digest, sparse landmarks.
- Purpose: enable immediate **PGO** to stabilize the global frame.

## L2 — Geometry Δ
- MUST contain: for each octree block `{block_id, resolution}` a list of voxel updates, each with either:
  - occupancy log-odds increment `ΔL` **OR**
  - TSDF distance increment `Δd` with weight `w_Δ`.
- SHOULD contain: view-angle or ray-count for weighting, timestamps.
- Receiver behavior: update global map as `L_new = clamp(L_old + ΔL)` or TSDF weighted average.

## L3 — Semantics Δ
- MUST contain: for each voxel, a compact encoding of class distribution delta (e.g., logit `Δz` or Dirichlet count `Δα`) and instance ID (or a merge-hint tuple).
- SHOULD contain: relation edges between instances, attribute updates.
- Receiver behavior: fuse probabilities (softmax/log-odds) and perform instance matching within overlap using IoU + class consistency.
