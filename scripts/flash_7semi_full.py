import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check 7Semi class definition
child.sendline("cat /home/arduino/Arduino/libraries/7Semi_BNO08x/src/7Semi_BNO08x.h | grep -A 30 'class ' | head -n 35")
child.expect(r'\$', timeout=10)

child.sendline("exit")
child.expect(pexpect.EOF)
