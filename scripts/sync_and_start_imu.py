import pexpect, sys

# 1. SCP updated imu_publisher.py to Uno Q
child = pexpect.spawn("scp -o StrictHostKeyChecking=no src/bno08x_ros/bno08x_ros/imu_publisher.py arduino@192.168.1.17:/home/arduino/pendrive/ros_ws/src/bno08x_ros/bno08x_ros/imu_publisher.py", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

# 2. SSH to restart container with socket mount and run IMU node
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker stop rplidar || true && docker rm rplidar || true")
child.expect([r'\$ '], timeout=30)

child.sendline("docker run -d --name rplidar --net=host -v /home/arduino/pendrive/ros_ws:/ws -v /var/run/arduino-router.sock:/var/run/arduino-router.sock --privileged -v /dev:/dev ros:jazzy-ros-base sleep infinity")
child.expect([r'\$ '], timeout=30)

# Rebuild in workspace
child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/jazzy/setup.bash && colcon build --packages-select bno08x_ros'")
child.expect([r'\$ '], timeout=60)

# Launch both Lidar and IMU
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && python3 -u /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
