import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    "echo '=== BLOCK DEVICES ===' && lsblk",
    "echo '=== DISK SPACE ===' && df -h",
    "echo '=== MEMORY ===' && free -h"
]

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
print(f"Connecting to {ssh_cmd}...")

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    # Handle password prompt
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if idx == 0:
        child.sendline(password)
    else:
        print("Failed to get password prompt")
        sys.exit(1)
        
    # Wait for shell prompt
    child.expect([r'\$', r'#'], timeout=10)
    
    # Run commands
    for cmd in commands:
        child.sendline(cmd)
        child.expect([r'\$', r'#'], timeout=15)
        
    child.sendline("exit")
    child.expect(pexpect.EOF)
except Exception as e:
    print(f"\n❌ Error during SSH: {e}")
