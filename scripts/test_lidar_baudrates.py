import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && ros2 launch rplidar_ros rplidar_a1_launch.py serial_port:=/dev/ttyUSB0 serial_baudrate:=115200 & sleep 5 && ros2 topic list && ros2 topic echo /scan --once'")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
