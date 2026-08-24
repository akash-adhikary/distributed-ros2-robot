import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Check docker status and start container if stopped
child.sendline("docker start rplidar || docker run -d --name rplidar --privileged --net=host -v /dev:/dev -v /mnt/pendrive/ros_ws:/ros_ws uno_ros_base tail -f /dev/null")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

child.sendline("docker ps")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
