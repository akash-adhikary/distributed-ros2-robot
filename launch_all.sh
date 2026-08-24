#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml

# Restart daemon to clear any bad cached discovery
ros2 daemon stop
ros2 daemon start

echo "Starting SLAM stack..."
ros2 launch my_robot_nav imu_slam.launch.py
