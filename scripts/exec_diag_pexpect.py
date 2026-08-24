import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/diag_runner.sh arduino@192.168.1.17:~/diag_runner.sh", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/diag_runner.sh")
child.expect([r'=== HARDWARE I2C BUS DIAGNOSTIC ==='], timeout=90)
child.expect([r'\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
