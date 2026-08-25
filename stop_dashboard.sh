#!/bin/bash
echo "Stopping Distributed ROS 2 Robot Control Hub..."

# Kill dashboard and bridge processes locally and inside docker
pkill -9 -f 'src/my_robot_dashboard/app.py|src/my_robot_dashboard/telemetry_bridge.py|qos_relay|slam_toolbox|rviz2' 2>/dev/null || true
docker exec -t thirsty_burnell pkill -9 -f 'src/my_robot_dashboard/app.py|src/my_robot_dashboard/telemetry_bridge.py|qos_relay|slam_toolbox|rviz2' 2>/dev/null || true

# Free port 5050 if held by zombie process
kill -9 $(lsof -ti:5050 2>/dev/null) 2>/dev/null || true
docker exec -t thirsty_burnell python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.close()" 2>/dev/null || true

# Remove stale pidfiles
rm -f /tmp/my_robot_dashboard.pid
docker exec -t thirsty_burnell rm -f /tmp/my_robot_dashboard.pid 2>/dev/null || true

echo "Dashboard stopped and port 5050 freed."
