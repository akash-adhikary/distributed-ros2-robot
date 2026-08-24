#!/bin/bash
set -e

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo "Starting LaserScan RViz visualizer (Fixed Frame: laser)..."
rviz2 -d /home/ros/my_robot_ws/src/my_robot_nav/config/laser_view.rviz
