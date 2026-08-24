import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec rplidar bash -c 'source /ros_entrypoint.sh && source /ros_ws/install/setup.bash && ros2 pkg list | grep rplidar'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
