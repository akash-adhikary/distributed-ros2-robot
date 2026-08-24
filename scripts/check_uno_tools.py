import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Check for arduino-cli, stm32 flasher tools, or internal bridge processes
commands = [
    "which arduino-cli || echo 'no arduino-cli'",
    "which dfu-util || echo 'no dfu-util'",
    "ls -la /dev/tty* /dev/rpmsg* /dev/remoteproc* 2>/dev/null",
    "ps aux | grep -iE 'bridge|rpc|remoteproc|arduino' | grep -v grep",
    "uname -a"
]

for cmd in commands:
    child.sendline(cmd)
    child.expect(r'\$', timeout=10)

child.sendline("exit")
child.expect(pexpect.EOF)
