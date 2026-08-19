#!/bin/bash
# 🤖 Start Robot Simulation (Gazebo + RViz2 + Bridge)

# Exit on error
set -e

# Default settings
HEADLESS=false

# Parse flags
for arg in "$@"; do
  case $arg in
    --headless)
      HEADLESS=true
      shift
      ;;
  esac
done

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash

# Build and source workspace
cd /home/ros/my_robot_ws
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4
source install/setup.bash

# Launch simulation
if [ "$HEADLESS" = true ]; then
  echo "Starting simulation in HEADLESS (server-only) mode..."
  ros2 launch my_robot_bringup sim_robot.launch.py headless:=true use_rviz:=false
else
  echo "Starting simulation in GUI mode..."
  ros2 launch my_robot_bringup sim_robot.launch.py headless:=false use_rviz:=true
fi
