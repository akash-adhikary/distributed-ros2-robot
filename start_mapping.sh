#!/bin/bash
set -e

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo "Starting 2D SLAM Mapping Stack & RViz on Laptop..."
ros2 launch my_robot_nav handheld_mapping.launch.py
