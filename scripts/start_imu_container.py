import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker rm -f bno08x_ros 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("docker run -d --restart=always --name bno08x_ros --net=host -v /var/run/arduino-router.sock:/var/run/arduino-router.sock -v /home/arduino/pendrive/ros_ws:/ros_ws -e ROS_DOMAIN_ID=42 ros:jazzy-ros-base bash -c 'source /opt/ros/jazzy/setup.bash && python3 /ros_ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'\$ '], timeout=30)

child.sendline("sleep 2 && docker logs bno08x_ros")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
