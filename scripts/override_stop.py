import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S mkdir -p /etc/systemd/system/arduino-router.service.d")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo -e '[Service]\\nExecStopPost=' | sudo tee /etc/systemd/system/arduino-router.service.d/99-override.conf")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("sudo systemctl daemon-reload")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("sudo systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
