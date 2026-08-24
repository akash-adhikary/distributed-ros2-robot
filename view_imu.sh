#!/bin/bash
set -e

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo "Starting IMU RViz visualizer & TF broadcaster on Laptop..."

# Start static transform for base_link -> imu_link in background
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link imu_link &
TF_PID=$!

trap "kill $TF_PID 2>/dev/null || true" EXIT

rviz2 -d /home/ros/my_robot_ws/src/my_robot_nav/config/imu_view.rviz
