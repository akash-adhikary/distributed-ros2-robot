import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S systemctl stop docker docker.socket")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("echo '{\"data-root\": \"/home/arduino/pendrive/docker\"}' | sudo -S tee /etc/docker/daemon.json")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S systemctl start docker")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("docker info | grep 'Docker Root Dir'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
