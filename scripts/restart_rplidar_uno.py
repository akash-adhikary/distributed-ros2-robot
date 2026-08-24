import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Stop and restart container to refresh socket mount
child.sendline("docker rm -f rplidar >/dev/null 2>&1 || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker run -d --name rplidar --restart always --privileged --net=host -v /dev:/dev -v /home/arduino/pendrive/ros_ws:/ws -v /var/run/arduino-router.sock:/var/run/arduino-router.sock uno_ros_base tail -f /dev/null")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

# Launch rplidar node
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 launch rplidar_ros rplidar_c1_launch.py'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

# Install msgpack
child.sendline("docker exec rplidar apt-get install -y python3-msgpack")
child.expect([r'arduino@blissy:\~\$ '], timeout=60)

# Launch imu node
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && python3 /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py > /tmp/imu_node.log 2>&1'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
