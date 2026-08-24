import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("find /usr/ -name '*app_utils*' 2>/dev/null || find /home/ -name '*app_utils*'")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
