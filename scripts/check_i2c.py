import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    child.expect('password:', timeout=10)
    child.sendline(password)
    child.expect(r'\$', timeout=10)
    
    child.sendline("sudo -S apt-get install -y i2c-tools")
    idx = child.expect(['password for arduino:', r'\$'], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'\$', timeout=60)
        
    child.sendline("sudo i2cdetect -y 0")
    child.expect(r'\$', timeout=10)
    
    child.sendline("sudo i2cdetect -y 1")
    child.expect(r'\$', timeout=10)
    
    child.sendline("sudo i2cdetect -y 2")
    child.expect(r'\$', timeout=10)

    child.sendline("exit")
    child.expect(pexpect.EOF)
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
