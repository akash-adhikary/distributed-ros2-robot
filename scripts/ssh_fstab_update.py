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
    # 1. Handle SSH password prompt
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if idx == 0:
        child.sendline(password)
    else:
        print("Failed to get password prompt")
        sys.exit(1)
        
    child.expect([r'\$', r'#'], timeout=10)
    
    # 2. Become root using sudo -S su -
    print("\nSwitching to root user...")
    child.sendline("sudo -S su -")
    idx = child.expect(['password for arduino:', r'#'], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'#', timeout=10)
        
    # 3. Unmount sda1
    print("\nUnmounting /dev/sda1...")
    child.sendline("umount /home/arduino/pendrive")
    child.expect(r'#', timeout=10)
    
    # 4. Update /etc/fstab with FAT32-specific mount options (uid=1000, gid=1000, umask=000)
    print("\nUpdating /etc/fstab for FAT32 permissions...")
    # Remove old entry if exists, and append the correct permission-mapped entry
    child.sendline("sed -i '\\|/dev/sda1|d' /etc/fstab")
    child.expect(r'#', timeout=10)
    child.sendline("echo '/dev/sda1 /home/arduino/pendrive vfat defaults,uid=1000,gid=1000,umask=000,nofail 0 2' >> /etc/fstab")
    child.expect(r'#', timeout=10)
    
    # 5. Remount all partitions from fstab
    print("\nRemounting partitions...")
    child.sendline("mount -a")
    child.expect(r'#', timeout=10)
    
    # 6. Exit root to verify as normal arduino user
    print("\nExiting root to verify normal user permissions...")
    child.sendline("exit")
    child.expect(r'\$', timeout=10)
    
    # 7. Write a test file as arduino user to confirm write permissions
    print("\nTesting write permission as normal user...")
    child.sendline("echo 'Uno Q is ready!' > /home/arduino/pendrive/test_write.txt")
    child.expect(r'\$', timeout=10)
    
    # Read the test file
    child.sendline("cat /home/arduino/pendrive/test_write.txt")
    child.expect(r'\$', timeout=10)
    
    child.sendline("exit")
    child.expect(pexpect.EOF)
    print("\n✅ USB Mount and Permissions configured successfully!")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
