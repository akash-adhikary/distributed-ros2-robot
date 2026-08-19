#!/bin/bash
# 💾 Save SLAM generated map files

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
cd /home/ros/my_robot_ws
source install/setup.bash

echo "Calling SLAM Toolbox map-saving service..."
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \
  "{name: {data: '/home/ros/my_robot_ws/src/my_robot_nav/maps/my_map'}}"

echo "Verifying saved map files in maps directory..."
ls -la /home/ros/my_robot_ws/src/my_robot_nav/maps/
