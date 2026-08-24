import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("tail -n 30 /var/log/dpkg.log")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("ps aux | grep apt")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
