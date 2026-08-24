import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo '=== UNO CPU/MEM ==='; free -h; top -bn1 | head -n 5; echo '=== UNO DISK ==='; df -h /")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
