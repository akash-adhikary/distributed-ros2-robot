import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S reboot")
child.expect(pexpect.EOF, timeout=15)
print("Uno Q reboot command issued successfully.")
