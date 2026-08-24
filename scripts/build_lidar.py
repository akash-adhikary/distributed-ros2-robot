import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/humble/setup.bash && colcon build'")
child.expect([r'\$ '], timeout=600)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && python3 -u /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec rplidar bash -c 'source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=42 && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && timeout 10 ros2 topic hz /scan || true'")
child.expect([r'\$ '], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
