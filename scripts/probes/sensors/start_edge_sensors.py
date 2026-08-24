#!/usr/bin/env python3
"""
Probe: Launch RPLidar C1 (10 Hz) and BNO086 IMU (100 Hz) on Uno Q Edge
Usage: python3 start_edge_sensors.py
"""
import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB0 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("docker start rplidar")
child.expect([r'\$ '], timeout=15)

# Terminate any previous instances
child.sendline("docker exec -t rplidar pkill -f 'rplidar_node|imu_publisher' 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

# Launch RPLidar
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'\$ '], timeout=15)

# Launch BNO086 IMU
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && python3 /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'\$ '], timeout=15)

child.sendline("sleep 2 && docker exec -t rplidar bash -c 'source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=42; ros2 topic list'")
child.expect([r'\$ '], timeout=15)

print("\n Edge sensors launched successfully on Uno Q.")
child.sendline("exit")
child.expect(pexpect.EOF)
