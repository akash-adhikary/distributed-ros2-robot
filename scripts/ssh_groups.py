import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
print(f"Connecting to {ssh_cmd}...")

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    child.expect(['password:'], timeout=10)
    child.sendline(password)
    child.expect([r'\$', r'#'], timeout=10)
    
    # Check groups
    child.sendline("groups")
    child.expect([r'\$', r'#'], timeout=10)
    
    # Check sudo privileges
    child.sendline("sudo -l")
    idx = child.expect(['[sudo] password for arduino:', r'\$', r'#'], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect([r'\$', r'#'], timeout=10)
        
    child.sendline("exit")
    child.expect(pexpect.EOF)
except Exception as e:
    print(f"\nError: {e}")
