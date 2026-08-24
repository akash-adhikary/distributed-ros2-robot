import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("while ps aux | grep -v grep | grep dpkg > /dev/null; do sleep 5; echo 'dpkg_active'; done; echo 'ALL_DONE_NOW'")
child.expect([r'\r\nALL_DONE_NOW\r\n'], timeout=1200)

child.sendline("exit")
child.expect(pexpect.EOF)
