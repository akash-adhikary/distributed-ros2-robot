import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router && echo ROUTER_RESTARTED")
child.expect([r'ROUTER_RESTARTED'], timeout=15)
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 ~/read_sock.py && echo SCRIPT_DONE")
child.expect([r'SCRIPT_DONE'], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
