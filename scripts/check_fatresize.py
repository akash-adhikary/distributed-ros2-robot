import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("which parted fatresize")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S parted /dev/sda print")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
