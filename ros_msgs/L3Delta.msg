string version
string frame_id
SemBlockDelta[] blocks

================================================================================
MSG: SemBlockDelta
string block_id
float64 resolution
SemVoxel[] voxels

================================================================================
MSG: SemVoxel
int32[3] ijk
float64[] logit_delta
float64[] dirichlet_delta
string    instance_id
string[]  merge_hint
