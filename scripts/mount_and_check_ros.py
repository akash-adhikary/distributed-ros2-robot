import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S mkdir -p /mnt/pendrive && sudo mount /dev/sda1 /mnt/pendrive || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("ls -la /mnt/pendrive && ls /dev/ttyUSB* /dev/rplidar /dev/i2c* 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
