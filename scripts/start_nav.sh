#!/bin/bash
# 🚀 Start Nav2 Autonomous Navigation

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
cd /home/ros/my_robot_ws
source install/setup.bash

echo "Starting Nav2 Navigation Stack (loading my_map.yaml)..."
ros2 launch my_robot_nav navigation.launch.py
