import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("which python3")
child.expect([r'\$ '], timeout=15)

child.sendline("python3 -c 'import rclpy; print(\"RCLPY_AVAILABLE\")' 2>/dev/null || echo 'RCLPY_NOT_INSTALLED'")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
