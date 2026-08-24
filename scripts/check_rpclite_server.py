import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("grep -rn 'bind' /home/arduino/Arduino/libraries/Arduino_RPClite/examples/ || ls /home/arduino/Arduino/libraries/Arduino_RPClite/examples/")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("cat /home/arduino/Arduino/libraries/Arduino_RPClite/src/Arduino_RPClite.h | head -n 45")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
