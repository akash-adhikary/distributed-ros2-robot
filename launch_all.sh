#!/bin/bash
set -e

echo "Starting SLAM stack on Laptop and edge sensors on Uno Q..."

# 1. Remotely launch Lidar and IMU on Uno Q via SSH
# We use docker exec -d to run them in the background natively.
ssh -o StrictHostKeyChecking=no arduino@192.168.1.17 << 'REMOTE'
    # Start Lidar
    docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0' || true
    
    # Start IMU (Temporarily commented out until we restore the IMU code)
    # docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && python3 -u /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py' || true
REMOTE

echo "Edge sensors launched successfully."

# 2. Launch Local SLAM stack
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://${PWD}/cyclonedds.xml

# Ensure CycloneDDS uses the correct network interface config
ros2 launch my_robot_bringup slam_launch.py
