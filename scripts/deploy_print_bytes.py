import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/print_frame_bytes.sh arduino@192.168.1.17:~/print_frame_bytes.sh", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/print_frame_bytes.sh")
child.expect([r'PRINT_BYTES_READY'], timeout=120)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
