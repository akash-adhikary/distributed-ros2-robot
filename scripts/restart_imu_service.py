import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart bno08x_ros.service 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl status bno08x_ros.service 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
