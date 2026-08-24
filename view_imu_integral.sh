#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect if running inside ROS container or on Host
if command -v ros2 &> /dev/null; then
    source /opt/ros/jazzy/setup.bash 2>/dev/null || true
    source /home/ros/my_robot_ws/install/setup.bash 2>/dev/null || true
    export ROS_DOMAIN_ID=42
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
    
    echo "Starting Pure Cumulative IMU Double-Integrator & RViz..."
    python3 /home/ros/my_robot_ws/src/my_robot_nav/scripts/imu_dead_reckoning_pure.py &
    TRACKER_PID=$!
    trap "kill $TRACKER_PID 2>/dev/null || true" EXIT
    
    rviz2 -d /home/ros/my_robot_ws/src/my_robot_nav/config/imu_view.rviz
else
    CONTAINER_ID=$(docker ps -q --filter "name=my_robot_ws" | head -n 1)
    if [ -z "$CONTAINER_ID" ]; then
        CONTAINER_ID="thirsty_burnell"
    fi
    echo "Forwarding to DevContainer ($CONTAINER_ID)..."
    xhost +local: 2>/dev/null || true
    docker exec -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix $CONTAINER_ID bash -c "
        source /opt/ros/jazzy/setup.bash
        source /home/ros/my_robot_ws/install/setup.bash 2>/dev/null || true
        export ROS_DOMAIN_ID=42
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
        export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
        python3 /home/ros/my_robot_ws/src/my_robot_nav/scripts/imu_dead_reckoning_pure.py &
        TRACKER_PID=\$!
        trap 'kill \$TRACKER_PID 2>/dev/null || true' EXIT
        rviz2 -d /home/ros/my_robot_ws/src/my_robot_nav/config/imu_view.rviz
    "
fi
