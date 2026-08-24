import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > ~/comp.log 2>&1")
child.expect([r'\$ '], timeout=120)

child.sendline("cat ~/comp.log")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
