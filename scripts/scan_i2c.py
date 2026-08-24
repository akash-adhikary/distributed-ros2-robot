import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("sudo apt-get install -y i2c-tools && sudo i2cdetect -y -r 0 && sudo i2cdetect -y -r 1 && sudo i2cdetect -y -r 2 || true")
child.expect([r'\[sudo\] password for arduino:', r'\$ '], timeout=15)
if 'password' in child.after:
    child.sendline("Askaban78@#")
    child.expect([r'\$ '], timeout=60)
else:
    child.expect([r'\$ '], timeout=60)

child.sendline("exit")
child.expect(pexpect.EOF)
