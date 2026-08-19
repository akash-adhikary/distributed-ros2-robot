#!/bin/bash
# Sets up DDS network routing and launches the handheld mapping stack on the laptop
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Source the workspace
source /opt/ros/*/setup.bash
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
fi

echo "🚀 Starting Handheld Mapping Mode..."
echo "Please walk SLOWLY with the Lidar to allow the laser scan matcher to track your movement."
ros2 launch my_robot_nav handheld_mapping.launch.py
