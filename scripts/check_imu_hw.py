import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("ls -l /dev/i2c* /dev/tty* /dev/serial* 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("i2cdetect -y 0 2>/dev/null || i2cdetect -y 1 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
