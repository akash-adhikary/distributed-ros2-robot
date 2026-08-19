#!/bin/bash
# 🛑 Stop all active ROS 2 and Gazebo sessions

echo "Terminating all active ROS 2, Gazebo, and RViz sessions..."
pkill -9 -f 'ros2|gz|rviz|slam|navigation|parameter_bridge' 2>/dev/null
sleep 1
echo "Cleanup completed successfully!"
