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
        
    # Wait for shell prompt
    child.expect([r'\$', r'#'], timeout=10)
    
    # 2. Become root using sudo -S su -
    print("\nSwitching to root user...")
    child.sendline("sudo -S su -")
    idx = child.expect(['password for arduino:', r'#'], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'#', timeout=10)
        
    # 3. Create mount folder
    print("\nCreating mount folder...")
    child.sendline("mkdir -p /home/arduino/pendrive")
    child.expect(r'#', timeout=10)
    
    # 4. Mount sda1
    print("\nMounting /dev/sda1...")
    child.sendline("mount /dev/sda1 /home/arduino/pendrive")
    child.expect(r'#', timeout=10)
    
    # 5. Change ownership to arduino:arduino
    print("\nChanging mount ownership...")
    child.sendline("chown -R arduino:arduino /home/arduino/pendrive")
    child.expect(r'#', timeout=10)
    
    # 6. Verify mount
    print("\nVerifying mount...")
    child.sendline("df -h /home/arduino/pendrive")
    child.expect(r'#', timeout=10)
    
    # 7. Configure automount in fstab
    print("\nConfiguring automount in fstab...")
    fstab_cmd = "grep -q '/dev/sda1' /etc/fstab || echo '/dev/sda1 /home/arduino/pendrive auto defaults,nofail 0 2' >> /etc/fstab"
    child.sendline(fstab_cmd)
    child.expect(r'#', timeout=10)
    
    # 8. Clean apt cache
    print("\nCleaning apt package cache...")
    child.sendline("apt-get clean && apt-get autoremove -y --purge")
    child.expect(r'#', timeout=30)
    
    # 9. Verify final disk space
    print("\nVerifying final disk space...")
    child.sendline("df -h")
    child.expect(r'#', timeout=10)
    
    child.sendline("exit") # exit root
    child.expect(r'\$', timeout=10)
    child.sendline("exit") # exit ssh
    child.expect(pexpect.EOF)
    print("\n✅ Setup and space optimization completed successfully!")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
