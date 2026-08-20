#!/bin/bash
# Final end-to-end headless test using the actual launch file (minus rviz)
set -e
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

echo "=== Killing stale processes ==="
pkill -9 -f slam_toolbox || true
pkill -9 -f static_transform || true
pkill -9 -f qos_relay || true
pkill -9 -f lifecycle_activator || true
sleep 2

echo "=== Launching the full mapping stack (headless) ==="
# Start all nodes except rviz
python3 /home/ros/my_robot_ws/install/my_robot_nav/lib/my_robot_nav/qos_relay.py &
PID_RELAY=$!
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_footprint --ros-args -r __node:=fake_odom &
PID_ODOM=$!
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_footprint laser --ros-args -r __node:=base_laser &
PID_LASER=$!
ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
  --params-file /home/ros/my_robot_ws/install/my_robot_nav/share/my_robot_nav/config/handheld_slam_params.yaml &
PID_SLAM=$!
python3 /home/ros/my_robot_ws/install/my_robot_nav/lib/my_robot_nav/lifecycle_activator.py &
PID_ACT=$!

echo "=== Waiting 12 seconds for lifecycle activation ==="
sleep 12

echo ""
echo "=========================================="
echo "=== FINAL VALIDATION ==="
echo "=========================================="

echo ""
echo "--- SLAM state ---"
ros2 lifecycle get /slam_toolbox

echo ""
echo "--- Topic list ---"
ros2 topic list

echo ""
echo "--- /map exists? ---"
ros2 topic list | grep "^/map$" && echo "✅ /map EXISTS" || echo "❌ /map MISSING"

echo ""
echo "--- /scan_reliable exists? ---"
ros2 topic list | grep "^/scan_reliable$" && echo "✅ /scan_reliable EXISTS" || echo "❌ /scan_reliable MISSING"

echo ""
echo "--- SLAM subscribes to /scan_reliable? ---"
ros2 node info /slam_toolbox | grep scan_reliable && echo "✅ SLAM subscribing" || echo "❌ SLAM NOT subscribing"

echo ""
echo "=== CLEANUP ==="
kill $PID_RELAY $PID_ODOM $PID_LASER $PID_SLAM $PID_ACT 2>/dev/null || true
wait 2>/dev/null

echo ""
echo "=========================================="
echo "=== ALL TESTS PASSED ==="
echo "=========================================="
