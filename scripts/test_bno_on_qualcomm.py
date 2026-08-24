import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 -c 'import smbus2, time; b=smbus2.SMBus(0); print(\"Bus 0 opened successfully\")' 2>&1 || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 -c 'import smbus2, time; b=smbus2.SMBus(1); print(\"Bus 1 opened successfully\")' 2>&1 || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
