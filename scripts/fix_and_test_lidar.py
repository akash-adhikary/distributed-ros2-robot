import pexpect, sys, time

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Remount /mnt/pendrive if unmounted after reboot
child.sendline("echo 'Askaban78@#' | sudo -S mount /dev/sda1 /mnt/pendrive 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Recreate rplidar container with pendrive volume
child.sendline("docker rm -f rplidar 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker run -d --name rplidar --restart always --privileged --net=host -v /dev:/dev -v /mnt/pendrive/ros_ws:/ros_ws uno_ros_base tail -f /dev/null")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

time.sleep(2)

# Fix permissions
child.sendline("echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB* 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Launch rplidar node in background
child.sendline("docker exec -d rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 launch rplidar_ros rplidar_a1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

time.sleep(4)

# Check topic echo
child.sendline("docker exec rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 topic echo /scan --once'")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
