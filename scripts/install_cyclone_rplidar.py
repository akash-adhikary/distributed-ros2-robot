import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec -t rplidar apt-get update && docker exec -t rplidar apt-get install -y ros-jazzy-rmw-cyclonedds-cpp")
child.expect([r'\$ '], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
