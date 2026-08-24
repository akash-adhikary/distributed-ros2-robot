import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("sudo reboot")
child.expect([r'[pP]assword for arduino:'], timeout=15)
child.sendline("Askaban78@#")

child.expect(pexpect.EOF, timeout=10)
