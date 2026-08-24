#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROBOT_IP="${UNOQ_IP:-192.168.1.17}"

echo "========================================================="
echo "  DISTRIBUTED ROS 2 SLAM FUSION LAUNCHER"
echo "  Sensors: RPLidar C1 (10 Hz) + BNO086 IMU (100 Hz)"
echo "  Fusion: EKF + SLAM Toolbox (Domain 42, CycloneDDS)"
echo "========================================================="

# 1. Start edge sensors on Uno Q
echo "Attempting to start edge sensors on Uno Q ($ROBOT_IP)..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 arduino@$ROBOT_IP "
    echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB0 2>/dev/null || true
    docker start rplidar
    docker exec -t rplidar pkill -f 'rplidar_node|imu_publisher' 2>/dev/null || true
    docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'
    docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && python3 /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'
" 2>/dev/null && echo "Edge sensors active on Uno Q." || echo "[WARN] Could not connect to Uno Q at $ROBOT_IP (start sensors manually or via Dashboard)."

# 2. Launch Local SLAM & EKF pipeline
if command -v ros2 &> /dev/null; then
    source /opt/ros/jazzy/setup.bash 2>/dev/null || true
    source /home/ros/my_robot_ws/install/setup.bash 2>/dev/null || true
    export ROS_DOMAIN_ID=42
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
    
    ros2 launch my_robot_nav imu_slam.launch.py
else
    CONTAINER_ID=$(docker ps -q --filter "name=my_robot_ws" | head -n 1)
    if [ -z "$CONTAINER_ID" ]; then
        CONTAINER_ID="thirsty_burnell"
    fi
    echo "Launching SLAM inside DevContainer ($CONTAINER_ID)..."
    xhost +local: 2>/dev/null || true
    docker exec -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix $CONTAINER_ID bash -c "
        source /opt/ros/jazzy/setup.bash
        source /home/ros/my_robot_ws/install/setup.bash 2>/dev/null || true
        export ROS_DOMAIN_ID=42
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
        export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
        ros2 launch my_robot_nav imu_slam.launch.py
    "
fi
