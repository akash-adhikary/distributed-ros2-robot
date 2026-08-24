import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("ps aux | grep arduino-cli")
child.expect([r'\$ '], timeout=15)

child.sendline("killall -9 arduino-cli openocd remoteocd 2>/dev/null || true")
child.expect([r'\$ '], timeout=15)

child.sendline("arduino-cli compile -v --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'\$ '], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
