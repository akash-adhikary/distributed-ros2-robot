import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/build_sparkfun_proper.sh arduino@192.168.1.17:~/build_sparkfun_proper.sh", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/build_sparkfun_proper.sh")
child.expect([r'SPARKFUN_FIRMWARE_RUNNING'], timeout=120)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
