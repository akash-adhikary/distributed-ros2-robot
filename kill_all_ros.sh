#!/bin/bash
echo "Killing all active ROS 2 SLAM, Relay, and Visualizer nodes..."
# Soft reset via API if dashboard is up, otherwise pkill directly
if curl -s -X POST http://localhost:5050/api/system/kill_all -H "Content-Type: application/json" -d '{}' >/dev/null 2>&1; then
    echo "Successfully signaled ROS node reset via Dashboard API."
else
    echo "Dashboard API unreachable, performing direct process cleanup..."
    pkill -9 -f 'qos_relay|slam_toolbox|rviz2|sync_slam_toolbox_node' 2>/dev/null || true
    docker exec -t thirsty_burnell pkill -9 -f 'qos_relay|slam_toolbox|rviz2|sync_slam_toolbox_node' 2>/dev/null || true
fi
echo "ROS node cleanup complete."
