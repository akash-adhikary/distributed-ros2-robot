import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no -r arduino@192.168.1.17:/home/arduino/pendrive/ros_ws/src/bno08x_ros src/", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=60)
