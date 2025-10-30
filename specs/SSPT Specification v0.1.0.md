#SSPT Specification v0.1.0
Streamed Submap Progressive Transmission

## 1. Purpose
This document defines the **three-layer, prefix-decodable** submap format used in our
paper “Centralized Mapping Driven by Progressive Coding”. It targets multi-robot
semantic mapping under bandwidth constraints.

## 2. Common header
Every transmitted layer message MUST contain the following fields.

| Field      | Type   | Description |
|------------|--------|-------------|
| `submap_id` | string | Unique identifier of the submap. |
| `robot_id`  | string | Source robot / agent. |
| `layer`     | uint8  | 1 = L1 skeleton, 2 = L2 geometry Δ, 3 = L3 semantics Δ. |
| `version`   | uint32 | Monotonic per (`submap_id`, `layer`). Enables idempotence. |
| `stamp`     | uint64 | Source timestamp (ns). |
| `payload`   | bytes / object | Layer-specific payload (see Sec. 3–5). |
| `crc`       | uint32 | OPTIONAL. If present, receivers MUST check. |

The header is **order-independent**: messages may arrive in any order.

## 3. Layer 1 — Skeleton (MANDATORY)
- Pose node(s) of the submap
- Odometry / loop-closure edges with information matrix
- Optional: calibration / frame info
- This layer MUST be sent with a positive minimal rate as it affects global consistency.

## 4. Layer 2 — Geometry Δ
Sparse updates to occupancy / TSDF w.r.t. the last sent version:
- voxel or block ID
- value Δ (log-odds or TSDF distance)
- weight
Receivers apply **additive + clamping** update.

## 5. Layer 3 — Semantics Δ
Sparse semantic / instance updates:
- voxel or block ID
- class distribution Δ or logits Δ
- optional instance ID / merge hint

Receivers apply **commutative, associative** merging so that `L1 → L2 → L3`,
`L1 → L3 → L2`, or only `L1` all produce a valid map.

## 6. On-the-fly interruption
The sender pushes layers in decreasing score
`s(k,ℓ) = Δu_{k,ℓ} − λ* Δc_{k,ℓ}` (see paper, Sec. IV).
If bandwidth drops, the sender simply stops; the receiver keeps the
“highest received layer” `h_k(t)` and fuses touched voxels only.
No rollback is needed.
