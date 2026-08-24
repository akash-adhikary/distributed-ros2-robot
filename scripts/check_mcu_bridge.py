import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check bridge logs or use arduino-app-cli / rpc monitoring
child.sendline("journalctl -u arduino-router.service -n 20 --no-pager 2>/dev/null || journalctl -n 20 --no-pager")
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
