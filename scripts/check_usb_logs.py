import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    "sudo dmesg | grep -i usb | tail -n 30",
    "ls -l /sys/class/typec/ || echo 'No typec class'",
    "cat /sys/kernel/debug/usb/devices | grep -E '^T|^D|^S' | tail -n 20 || echo 'No debugfs usb devices'"
]

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    child.expect('password:', timeout=10)
    child.sendline(password)
    child.expect(r'\$', timeout=10)
    
    for cmd in commands:
        if cmd.startswith("sudo"):
            child.sendline(f"sudo -S {cmd.split(' ', 1)[1]}")
            idx = child.expect(['password for arduino:', r'\$'], timeout=10)
            if idx == 0:
                child.sendline(password)
                child.expect(r'\$', timeout=10)
        else:
            child.sendline(cmd)
            child.expect(r'\$', timeout=10)
        
    child.sendline("exit")
    child.expect(pexpect.EOF)
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
