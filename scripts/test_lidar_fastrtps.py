import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /home/arduino/pendrive/ros_ws/install/setup.bash 2>/dev/null || true && export ROS_DOMAIN_ID=42 && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'\$ '], timeout=15)

child.sendline("sleep 3")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -t rplidar bash -c 'source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=42; ros2 topic list'")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
