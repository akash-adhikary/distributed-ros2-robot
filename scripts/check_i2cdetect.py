import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("which i2cdetect || echo 'NO_I2CDETECT'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S i2cdetect -y -r 0 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S i2cdetect -y -r 1 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S i2cdetect -y -r 2 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
