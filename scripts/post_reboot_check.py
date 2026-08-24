import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Mount pendrive
child.sendline("echo 'Askaban78@#' | sudo -S mount /dev/sda1 /mnt/pendrive 2>/dev/null || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Start rplidar docker container
child.sendline("docker start rplidar")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
