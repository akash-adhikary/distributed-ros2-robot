import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("find ~/Arduino/libraries -name '*7Semi*' -o -name '*BNO08x*' 2>/dev/null")
child.expect([r'\$ '], timeout=15)

child.sendline("find ~/.arduino15/libraries ~/Arduino/libraries -name '*.h' | grep -i bno || true")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
