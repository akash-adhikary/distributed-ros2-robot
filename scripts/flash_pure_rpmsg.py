import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Check OpenOCD reset / boot status
child.sendline("echo 'Askaban78@#' | sudo -S systemctl status arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Try running arduino-cli monitor with explicit network port
child.sendline("timeout 5 arduino-cli monitor -p $(arduino-cli board list | grep unoq | awk '{print $1}') --fqbn arduino:zephyr:unoq || echo 'Monitor done'")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
