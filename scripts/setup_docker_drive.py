import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Stop docker
child.sendline("echo Askaban78@# | sudo -S systemctl stop docker docker.socket")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

# Unmount pendrive
child.sendline("echo Askaban78@# | sudo -S umount /home/arduino/pendrive")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Wipe partition table and create new ext4 partition
child.sendline("echo Askaban78@# | sudo -S parted /dev/sda mklabel gpt -s")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)
child.sendline("echo Askaban78@# | sudo -S parted /dev/sda mkpart primary ext4 0% 100% -s")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Format to ext4
child.sendline("echo Askaban78@# | sudo -S mkfs.ext4 -F /dev/sda1")
child.expect([r'arduino@blissy:\~\$ '], timeout=120)

# Get UUID
child.sendline("UUID=$(sudo blkid -s UUID -o value /dev/sda1); echo \"UUID=$UUID\"")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Remove old fstab entry for pendrive if it exists, and add new one
child.sendline("echo Askaban78@# | sudo -S sed -i '/pendrive/d' /etc/fstab")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo Askaban78@# | sudo -S bash -c \"echo \\\"UUID=\$(sudo blkid -s UUID -o value /dev/sda1) /home/arduino/pendrive ext4 defaults,nofail 0 2\\\" >> /etc/fstab\"")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Mount it
child.sendline("echo Askaban78@# | sudo -S mount -a")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Create docker directory and set permissions
child.sendline("echo Askaban78@# | sudo -S mkdir -p /home/arduino/pendrive/docker")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Configure docker daemon.json
child.sendline("echo Askaban78@# | sudo -S bash -c \"cat > /etc/docker/daemon.json << 'INNEREOF'\\n{\\n  \\\"data-root\\\": \\\"/home/arduino/pendrive/docker\\\"\\n}\\nINNEREOF\"")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Optional: Wipe old docker data on mmcblk to free up space completely
child.sendline("echo Askaban78@# | sudo -S rm -rf /var/lib/docker/*")
child.expect([r'arduino@blissy:\~\$ '], timeout=60)

# Start docker
child.sendline("echo Askaban78@# | sudo -S systemctl start docker")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

# Verify
child.sendline("docker info | grep 'Docker Root Dir'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("df -h /home/arduino/pendrive")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
