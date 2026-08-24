import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'\$ '], timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'\$ '], timeout=15)

child.sendline("sleep 2")
child.expect([r'\$ '], timeout=15)

child.sendline("python3 ~/check_d2.py")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
