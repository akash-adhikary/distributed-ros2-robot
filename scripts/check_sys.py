import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    child.expect('password:', timeout=10)
    child.sendline(password)
    child.expect(r'\$', timeout=10)

    child.sendline("sudo -S gpioinfo")
    idx = child.expect(['password for arduino:', r'\$'], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'\$', timeout=10)

    child.sendline("exit")
    child.expect(pexpect.EOF)
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
