import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec rplidar apt-get install -y python3-msgpack > /dev/null 2>&1")
child.expect([r'\$ '], timeout=60)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && python3 -u /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
