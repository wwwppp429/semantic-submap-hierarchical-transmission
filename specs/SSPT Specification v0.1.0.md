# Semantic Submap Hierarchical Transmission (SSHT)
### Specification v0.1.0 (companion to the paper)

> **Scope.**
> This document defines a *minimal* on-wire format 
for
 layered semantic
> submaps used 
in our paper 
"Feedback-Guided Hierarchical Transmission for
> Multi-Robot Mapping"
. It matches the public repository:
> `https://github.com/wwwppp429/semantic-submap-hierarchical-transmission`.
> It is **not** the full SLAM system code.

---

## 1. Terminology

- **Layer**: Logical level of a submap (L1 Skeleton, L2 Geometry, L3 Semantics).
- **Prefix-decodable**: Any prefix of received layers (e.g. L1 or L1+L2) yields a valid map.
- **Order-independent**: Packets can be applied 
in
 any order (commutative fusion).

The detailed semantics of each layer are 
in
 `layers.md`.
The mathematical model is 
in
 `prefix_model.md`.


## 2. Top-level message format (JSON Lines)

All messages are UTF-8 JSON objects, one per line.
A stream **MUST** begin with an optional header, followed by packet lines.

### 2.1 Header (Optional)
jsonc
{
  "type": "header"
,
  "format_version": "0.1.0"
,
  "note": "Demo trace."
,
  "crc32": 0  // Optional checksum for
 the header itself
}
## 2.2 Packet (Data)


{
  "type": "packet"
,
  "submap_id": 0,      // Integer or String ID
  "robot_id": 1,       // Source robot ID
  "layer": 2,          // 1=L1, 2=L2, 3=L3 (See Section 3)
  "version": 17,       // Monotonic version per (submap, layer)
  "stamp": 171000123,  // Timestamp (ns or ms)
  "payload": { ... },  // Layer-specific data
  "crc32": 1234567890  // Standard CRC32 of the JSON object (excluding this field)
}
## Implementation Requirements:
## 1. CRC32: Senders SHOULD compute crc32. Receivers MUST validate it if present.
## 2. Ignorance: Receivers MUST ignore unknown fields (forward compatibility).
## 3. Layer identifiers and meaning (MANDATORY)

For `packet` messages, the `layer` field defines the content type.

| `layer` | Name | Description |
| :--- | :--- | :--- |
| **1** | **L1 Skeleton** | **Mandatory.** Pose graph nodes, edges, and minimal meta-data. Ensures global consistency. |
| **2** | **L2 Geometry Δ** | **Optional.** Sparse occupancy or TSDF increments (log-odds). Fused via addition+clamping. |
| **3** | **L3 Semantics Δ** | **Optional.** Semantic class counts or instance hints. Fused via histogram accumulation. |

*See `layers.md` for the normative definition of payloads.*


## 4. Transmission & Interruption Model
1. Priority: The sender transmits layers in decreasing utility-to-cost ratio:
s = Δu - λ * Δc.
2. Interruption: If bandwidth drops, transmission stops.
The receiver keeps the "highest received layer" h_k(t) for each submap.
3. No Rollback: Due to the prefix-decodable design, partial uploads are valid. There is no need to discard incomplete submaps.
## 5. Payload Encoding
To keep JSON compact, binary payloads (like voxel arrays) use a b64z container:


{
  "codec": "b64z"
,
  "dtype": "int16"
,
  "shape"
: [1024],
  "data": "<base64_string_of_zlib_compressed_bytes>"
}
