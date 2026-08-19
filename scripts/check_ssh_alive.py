import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    "uptime",
    "lsusb"
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
        
        print("\n--- Connected Successfully! Running checks ---")
        for cmd in commands:
            child.sendline(cmd)
            child.expect(r'\$', timeout=10)
            
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n--- Disconnected Successfully ---")
    else:
        print("\n❌ Failed to connect or timed out.")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
