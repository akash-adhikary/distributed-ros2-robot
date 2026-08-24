import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/patch_perfect_bno.py arduino@192.168.1.17:~/patch_perfect_bno.py", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("python3 ~/patch_perfect_bno.py")
child.expect([r'PERFECT_BNO_BUS_WRITTEN'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/build_live_imu_all.sh")
child.expect([r'LIVE_IMU_ALL_READY'], timeout=120)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
