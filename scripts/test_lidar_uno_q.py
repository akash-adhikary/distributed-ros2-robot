import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    "sudo -S apt-get update && sudo apt-get install -y python3-serial",
    "cat << 'EOF' > /home/arduino/spin_test.py\nimport serial, time\ntry:\n    s = serial.Serial('/dev/ttyUSB0', 460800, timeout=1)\n    s.write(b'\\xA5\\x20')\n    print('Sent start command!')\n    time.sleep(2)\n    s.close()\nexcept Exception as e:\n    print(f'Error: {e}')\nEOF",
    "sudo chmod a+rw /dev/ttyUSB0",
    "python3 /home/arduino/spin_test.py"
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
        
        for cmd in commands:
            if cmd.startswith("sudo -S"):
                child.sendline(cmd)
                idx2 = child.expect(['password for arduino:', r'\$'], timeout=10)
                if idx2 == 0:
                    child.sendline(password)
                    child.expect(r'\$', timeout=60) # apt update might take a bit
            else:
                child.sendline(cmd)
                child.expect(r'\$', timeout=20)
                
        child.sendline("exit")
        child.expect(pexpect.EOF)
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
