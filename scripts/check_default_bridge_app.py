import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("cat /etc/systemd/system/arduino-router.service || cat /lib/systemd/system/arduino-router.service")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("ls -la /home/arduino/Arduino/libraries/Arduino_RouterBridge/extras/test/test_rpc_thread/python/")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("cat /home/arduino/Arduino/libraries/Arduino_RouterBridge/extras/test/test_rpc_thread/python/main.py")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
