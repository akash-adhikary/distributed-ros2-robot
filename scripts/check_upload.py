import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check upload port list and upload using standard local target
child.sendline("arduino-cli board list")
child.expect(r'\$', timeout=10)

child.sendline("arduino-cli upload -p $(arduino-cli board list | grep 'unoq' | awk '{print $1}') --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
