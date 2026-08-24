import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Clean up override config on systemd if created
child.sendline("echo 'Askaban78@#' | sudo -S rm -f /etc/systemd/system/arduino-router.service.d/99-override.conf")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("sudo systemctl daemon-reload && sudo systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

# Check mounted filesystems, usb pendrive, docker containers
child.sendline("df -h && lsblk && docker ps -a")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
