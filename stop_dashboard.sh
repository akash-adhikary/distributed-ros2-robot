#!/bin/bash
echo "Stopping Distributed ROS 2 Robot Control Hub..."

# 1. Kill dashboard, telemetry, qos_relay, SLAM and RViz inside DevContainer
docker exec -t thirsty_burnell bash -c '
  pkill -9 -f "app.py|qos_relay|slam_toolbox|rviz2|sync_slam_toolbox_node" 2>/dev/null || true
  rm -f /tmp/my_robot_dashboard.pid /tmp/my_robot_dashboard.lock
' 2>/dev/null || true

# 2. Kill any host-level instances
pkill -9 -f "app.py|qos_relay|slam_toolbox|rviz2|sync_slam_toolbox_node" 2>/dev/null || true
rm -f /tmp/my_robot_dashboard.pid /tmp/my_robot_dashboard.lock

echo "All ROS nodes, bridges, and dashboard processes terminated cleanly."
