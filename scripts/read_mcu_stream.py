import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Connect to the Arduino RPC / Router socket or serial channel to see MCU output
child.sendline("timeout 8 socat - UNIX-CONNECT:/var/run/arduino-router.sock 2>/dev/null || echo 'Socket check done'")
child.expect(r'\$', timeout=12)

child.sendline("dmesg | tail -n 25")
child.expect(r'\$', timeout=10)

child.sendline("exit")
child.expect(pexpect.EOF)
