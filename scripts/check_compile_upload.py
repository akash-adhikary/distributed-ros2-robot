import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Restart router
child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=60)

child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
idx = child.expect([r'arduino@blissy:\~\$', r'\$', pexpect.TIMEOUT], timeout=120)
if idx == 2:
    print("UPLOAD TIMED OUT!")

child.sendline("exit")
child.expect(pexpect.EOF)
