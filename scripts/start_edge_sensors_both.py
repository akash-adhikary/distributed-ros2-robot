import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB0")
child.expect([r'\$ '], timeout=15)

child.sendline("docker start rplidar")
child.expect([r'\$ '], timeout=15)

# Kill any previous node inside container
child.sendline("docker exec -t rplidar pkill -f 'rplidar_node|imu_publisher' 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

# Start RPLidar in background
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'\$ '], timeout=15)

# Start IMU in background
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && python3 /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'\$ '], timeout=15)

child.sendline("sleep 3")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -t rplidar bash -c 'source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=42; ros2 topic list'")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
