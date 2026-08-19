#!/bin/bash
# 🛰️ Start Physical RPLIDAR C1 Node using compiled official driver

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
cd /home/ros/my_robot_ws
source install/setup.bash

# Identify serial port
PORT="/dev/ttyUSB0"
if [ ! -e "$PORT" ]; then
    PORT="/dev/ttyACM0"
fi

if [ ! -e "$PORT" ]; then
    echo "❌ ERROR: No RPLIDAR device found at /dev/ttyUSB0 or /dev/ttyACM0!"
    exit 1
fi

echo "Found RPLIDAR at $PORT. Starting C1 launch file..."

# Launch the official RPLIDAR C1 driver launch file
ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:="$PORT"
