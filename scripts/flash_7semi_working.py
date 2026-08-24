import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check example sketch in 7Semi library
child.sendline("cat /home/arduino/Arduino/libraries/7Semi_BNO08x/examples/*/*.ino | head -n 45")
child.expect(r'\$', timeout=10)

child.sendline("exit")
child.expect(pexpect.EOF)
