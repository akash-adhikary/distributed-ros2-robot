import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/test_i2c_err_codes.sh arduino@192.168.1.17:~/test_i2c_err_codes.sh", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/test_i2c_err_codes.sh")
child.expect([r'=== I2C BUS TRANSMISSION STATUS ==='], timeout=120)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
