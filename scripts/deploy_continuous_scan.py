import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/continuous_i2c_scanner.sh arduino@192.168.1.17:~/continuous_i2c_scanner.sh", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/continuous_i2c_scanner.sh")
child.expect([r'\$ '], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
