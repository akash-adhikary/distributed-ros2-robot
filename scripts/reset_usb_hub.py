import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Reset USB hub or check USB tree
child.sendline("ls -l /dev/ttyUSB* /dev/serial/by-id/* 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Run rplidar_node directly without launch file to see exact error
child.sendline("docker exec rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && ros2 run rplidar_ros rplidar_node --ros-args -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=115200 -p frame_id:=laser_frame'")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
