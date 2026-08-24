import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -t bno08x_ros bash -c 'source /opt/ros/jazzy/setup.bash; timeout 3 ros2 topic echo /imu/data --once'")
child.expect([r'header:'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
