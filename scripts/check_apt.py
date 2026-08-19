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
    child.expect('password:', timeout=10)
    child.sendline(password)
    child.expect(r'\$', timeout=10)
    
    child.sendline("apt-cache search '^ros-[a-z]+-desktop' || echo 'Not found'")
    child.expect(r'\$', timeout=10)

    child.sendline("apt-cache search 'ros-core' || echo 'Not found'")
    child.expect(r'\$', timeout=10)
    
    child.sendline("apt-cache search 'rplidar' || echo 'Not found'")
    child.expect(r'\$', timeout=10)

    child.sendline("exit")
    child.expect(pexpect.EOF)
    
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
