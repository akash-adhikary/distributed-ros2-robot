import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S pkill -9 apt")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S pkill -9 dpkg")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S dpkg --configure -a")
child.expect([r'arduino@blissy:\~\$ '], timeout=120)

child.sendline("echo Askaban78@# | sudo -S DEBIAN_FRONTEND=noninteractive APT_LISTCHANGES_FRONTEND=none apt upgrade -y -o Dpkg::Options::=\"--force-confdef\" -o Dpkg::Options::=\"--force-confold\"")
child.expect([r'arduino@blissy:\~\$ '], timeout=600)

child.sendline("exit")
child.expect(pexpect.EOF)
