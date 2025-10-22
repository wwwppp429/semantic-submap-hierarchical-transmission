string version
string frame_id
time   stamp
SubmapNode[] submaps
Edge[] edges

================================================================================
MSG: SubmapNode
string id
geometry_msgs/Pose pose
float64[] info

================================================================================
MSG: Edge
string i
string j
string type
float64[] info
