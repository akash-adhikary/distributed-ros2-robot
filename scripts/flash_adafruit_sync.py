import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Compile
child.sendline("arduino-cli compile -v --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=180)

# Upload
child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=60)

# Restart router
child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
