import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("lsusb")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat /home/arduino/Arduino/libraries/Arduino_RouterBridge/examples/monitor/monitor.ino | head -n 30")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
