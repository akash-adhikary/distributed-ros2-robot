#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Clean up previous instances
pkill -9 -f "app.py|telemetry_bridge|qos_relay|slam_toolbox|rviz2" 2>/dev/null || true
docker exec -t thirsty_burnell bash -c 'pkill -9 -f "app.py|telemetry_bridge|qos_relay|slam_toolbox|rviz2" 2>/dev/null || true' 2>/dev/null || true


echo "========================================================="
echo "  STARTING DISTRIBUTED ROS 2 ROBOT CONTROL HUB"
echo "  Web UI: http://localhost:5050"
echo "========================================================="

# Detect if running inside ROS 2 container or on host
if command -v ros2 &> /dev/null; then
    source /opt/ros/jazzy/setup.bash 2>/dev/null || true
    source /home/ros/my_robot_ws/install/setup.bash 2>/dev/null || true
    export ROS_DOMAIN_ID=42
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
    export PORT=5050
    export DISPLAY=:0
    export QT_X11_NO_MITSHM=1
    
    python3 /home/ros/my_robot_ws/src/my_robot_dashboard/app.py
else
    CONTAINER_ID=$(docker ps -q --filter "name=my_robot_ws" | head -n 1)
    if [ -z "$CONTAINER_ID" ]; then
        CONTAINER_ID="thirsty_burnell"
    fi
    echo "Launching Dashboard inside DevContainer ($CONTAINER_ID)..."
    xhost +local: 2>/dev/null || true
    docker exec -it -e DISPLAY=$DISPLAY -e QT_X11_NO_MITSHM=1 $CONTAINER_ID bash -c "
        source /opt/ros/jazzy/setup.bash
        source /home/ros/my_robot_ws/install/setup.bash 2>/dev/null || true
        export ROS_DOMAIN_ID=42
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
        export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
        export PORT=5050
        export DISPLAY=:0
        export QT_X11_NO_MITSHM=1
        
        python3 /home/ros/my_robot_ws/src/my_robot_dashboard/app.py
    "

fi
