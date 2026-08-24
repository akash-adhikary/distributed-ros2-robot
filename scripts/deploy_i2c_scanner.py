import pexpect, sys

child = pexpect.spawn("scp -o StrictHostKeyChecking=no scripts/i2c_scanner.sh arduino@192.168.1.17:~/i2c_scanner.sh", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(pexpect.EOF, timeout=30)

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/i2c_scanner.sh")
child.expect([r'SCANNER_READY'], timeout=120)
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'PYEOF' > ~/check_i2c_scan.py
import socket, msgpack, time

def call_mcu(s, m):
    try:
        s.sendall(msgpack.packb([0, 1, m, []]))
        time.sleep(0.01)
        buf = s.recv(1024)
        u = msgpack.Unpacker()
        u.feed(buf)
        for msg in u: return msg[3]
    except: pass
    return None

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
found = call_mcu(s, 'i2c/found')
print('=== I2C HARDWARE SCAN RESULT ===')
if found and found > 0:
    print(f'>> SENSOR FOUND AT I2C ADDRESS: {hex(found)} ({found}) <<')
else:
    print('>> NO I2C DEVICE ACKNOWLEDGED ON THE BUS <<')
s.close()
PYEOF
python3 ~/check_i2c_scan.py
""")
child.expect([r'=== I2C HARDWARE SCAN RESULT ==='], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
