import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("grep -n -C 5 -i 'i2c' /home/arduino/.arduino15/packages/arduino/hardware/zephyr/0.90.0/firmwares/zephyr-arduino_uno_q_stm32u585xx.dts")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
