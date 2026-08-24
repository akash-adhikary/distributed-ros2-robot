import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=15)
child.sendline("ls -l /dev/spidev* 2>/dev/null || echo 'No spidev'")
child.expect(r'\$', timeout=15)
child.sendline("ls -l /dev/ttyMSM* /dev/ttyHS* /dev/ttyTHS* 2>/dev/null || echo 'No extra tty'")
child.expect(r'\$', timeout=15)
child.sendline("exit")
child.expect(pexpect.EOF)
