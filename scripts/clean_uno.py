import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S apt autoremove -y && sudo apt clean")
child.expect([r'arduino@blissy:\~\$ '], timeout=120)

child.sendline("echo '=== DISK INFO ==='; df -h")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo '=== DOCKER ROOT ==='; docker info | grep 'Docker Root Dir'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
