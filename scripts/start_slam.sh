#!/bin/bash
# 🗺️ Start SLAM Toolbox (Mapping)

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
cd /home/ros/my_robot_ws
source install/setup.bash

echo "Starting SLAM mapping node..."
ros2 launch my_robot_nav slam.launch.py
