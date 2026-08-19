#!/bin/bash
# ⌨️ Start Keyboard Teleop (Manual Driving Control)

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
cd /home/ros/my_robot_ws
source install/setup.bash

echo "Starting teleop keyboard controller..."
echo "Keep this terminal tab active and use keys (i, j, l, u, etc.) to drive."
ros2 run teleop_twist_keyboard teleop_twist_keyboard
