#!/bin/bash
echo "Resetting ROS nodes and visualizers..."

# Kill all SLAM, TF relays, and visualizer nodes on both container and host
docker exec -t thirsty_burnell bash -c '
  pkill -9 -f "qos_relay|slam_toolbox|rviz2|sync_slam_toolbox_node" 2>/dev/null || true
' 2>/dev/null || true

pkill -9 -f "qos_relay|slam_toolbox|rviz2|sync_slam_toolbox_node" 2>/dev/null || true

echo "ROS nodes reset complete."
