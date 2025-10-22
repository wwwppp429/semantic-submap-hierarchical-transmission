string version
string frame_id
BlockDelta[] blocks

================================================================================
MSG: BlockDelta
string block_id
float64 resolution
VoxelUpdate[] voxels

================================================================================
MSG: VoxelUpdate
int32[3] ijk
float64 dL
float64 dd
float64 w_delta
time     ts
