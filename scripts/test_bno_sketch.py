import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check installed arduino libraries and search for BNO08x
commands = [
    "arduino-cli lib list",
    "arduino-cli lib search bno08x"
]

for cmd in commands:
    child.sendline(cmd)
    child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
