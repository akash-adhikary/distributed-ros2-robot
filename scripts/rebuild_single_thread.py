import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

command = "sudo -S docker run --rm -v /home/arduino/pendrive/ros_ws:/ws uno_ros_base bash -c 'source /opt/ros/humble/setup.bash && cd /ws && export MAKEFLAGS=\"-j1\" && colcon build --executor sequential'"

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
print(f"Connecting to {ssh_cmd}...")

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'\$', timeout=10)
        
        print(f"\n---> Executing single thread build...")
        child.sendline(command)
        
        idx2 = child.expect(['password for arduino:', r'\$'], timeout=10)
        if idx2 == 0:
            child.sendline(password)
            
        child.expect(r'\$', timeout=600)
                
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n✅ Single-threaded build completed!")
    else:
        print("\n❌ Failed to connect.")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
