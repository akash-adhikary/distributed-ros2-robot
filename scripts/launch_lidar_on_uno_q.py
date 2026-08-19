import pexpect
import sys
import time

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

command = "/home/arduino/start_rplidar.sh"

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
print(f"Connecting to {ssh_cmd}...")

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'\$', timeout=10)
        
        print(f"\n---> Launching Lidar node on Uno Q...")
        child.sendline(command)
        
        # It might ask for sudo password inside the script
        idx2 = child.expect(['password for arduino:', r'\$'], timeout=10)
        if idx2 == 0:
            child.sendline(password)
            
        child.expect(r'\$', timeout=30)
                
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n✅ Node Launched Successfully!")
    else:
        print("\n❌ Failed to connect.")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
