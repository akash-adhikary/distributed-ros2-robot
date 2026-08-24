#!/bin/bash
set -e

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo "Starting Dynamic IMU-to-TF Visualizer & RViz on Laptop..."

# Run dynamic IMU-to-TF broadcaster in background
python3 /home/ros/my_robot_ws/src/my_robot_nav/scripts/imu_tf_broadcaster.py &
TF_PID=$!

trap "kill $TF_PID 2>/dev/null || true" EXIT

rviz2 -d /home/ros/my_robot_ws/src/my_robot_nav/config/imu_view.rviz
