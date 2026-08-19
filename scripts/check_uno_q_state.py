import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    "lsusb",
    "sudo -S docker ps --filter 'name=rplidar' --format '{{.Status}}'"
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
        
        print("\n--- Checking Uno Q Status ---")
        for cmd in commands:
            if cmd.startswith("sudo -S"):
                child.sendline(cmd)
                idx2 = child.expect(['password for arduino:', r'\$'], timeout=10)
                if idx2 == 0:
                    child.sendline(password)
                    child.expect(r'\$', timeout=10)
            else:
                child.sendline(cmd)
                child.expect(r'\$', timeout=10)
                
        child.sendline("exit")
        child.expect(pexpect.EOF)
    else:
        print("\n❌ Failed to connect. Board might be off.")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
