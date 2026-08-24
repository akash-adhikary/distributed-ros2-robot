import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("source /opt/ros/jazzy/setup.bash 2>/dev/null || source /opt/ros/humble/setup.bash 2>/dev/null; source /home/arduino/pendrive/ros_ws/install/setup.bash 2>/dev/null; ros2 topic echo /imu/data --max-count 2")
child.expect([r'\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
