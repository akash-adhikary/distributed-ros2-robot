import pexpect, sys, time

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check if compile finished or run upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

child.sendline("arduino-cli upload -p network --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=60)

# Read MCU serial output via arduino-router or monitor
child.sendline("timeout 10 arduino-cli monitor -p network -c baudrate=115200 || cat /var/log/syslog | grep MCU | tail -n 20")
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
