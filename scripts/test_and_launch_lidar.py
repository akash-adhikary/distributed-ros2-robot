import pexpect, sys, time

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Reset any hanging rplidar processes
child.sendline("docker exec rplidar pkill -9 -f rplidar || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Make sure permissions are right
child.sendline("echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB0 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Launch rplidar node in background
child.sendline("docker exec -d rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 launch rplidar_ros rplidar_a1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

time.sleep(3)

# Check topics
child.sendline("docker exec rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 topic list'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
