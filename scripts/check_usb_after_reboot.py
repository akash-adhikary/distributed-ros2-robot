import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    "uptime",
    "lsusb",
    "ls -l /dev/ttyUSB* || echo 'No ttyUSB found'",
    "df -h | grep pendrive || echo 'Pendrive not mounted'"
]

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
print(f"Connecting to {ssh_cmd}...")

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'\$', timeout=10)
        
        print("\n--- Running Diagnostics after Reboot ---")
        for cmd in commands:
            child.sendline(cmd)
            child.expect(r'\$', timeout=10)
            
        child.sendline("exit")
        child.expect(pexpect.EOF)
    else:
        print("\n❌ Failed to connect. Board might still be booting.")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
