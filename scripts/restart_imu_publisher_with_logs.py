import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec rplidar pkill -f imu_publisher.py || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && python3 -u /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py > /tmp/imu_node.log 2>&1'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("sleep 2 && docker exec rplidar cat /tmp/imu_node.log")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
