import pexpect, sys, time

for attempt in range(10):
    try:
        child = pexpect.spawn("ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 arduino@192.168.1.17", encoding='utf-8')
        child.logfile = sys.stdout
        res = child.expect([r'[pP]assword:', pexpect.TIMEOUT, pexpect.EOF], timeout=6)
        if res == 0:
            child.sendline("Askaban78@#")
            child.expect([r'\$ '], timeout=10)
            print("Uno Q is ONLINE and READY!")
            child.sendline("uptime")
            child.expect([r'\$ '], timeout=10)
            child.sendline("exit")
            child.expect(pexpect.EOF)
            sys.exit(0)
    except Exception as e:
        print(f"Attempt {attempt+1}: waiting for Uno Q... ({e})")
        time.sleep(3)

print("Uno Q did not come online in time.")
sys.exit(1)
