## 2. Common header

| Field      | Type   | Description |
|------------|--------|-------------|
| submap_id  | string | Unique ID of the submap |
| robot_id   | string | Source robot / agent |
| layer      | uint8  | 1 = L1 skeleton, 2 = L2 geometry Δ, 3 = L3 semantics Δ |
| version    | uint32 | Monotonic per (submap_id, layer) |
| stamp      | uint64 | Source timestamp |
| payload    | bytes  | Layer-specific data |
| crc        | uint32 | Optional, for idempotence |
