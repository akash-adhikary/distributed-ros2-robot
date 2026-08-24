import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

script = """cat << 'PYEOF' > ~/check_motion.py
import socket, msgpack, time
def call_mcu(s, m):
    s.sendall(msgpack.packb([0, 1, m, []]))
    time.sleep(0.02)
    buf = s.recv(1024)
    u = msgpack.Unpacker()
    u.feed(buf)
    for msg in u: return msg[3]
    return None
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
print('=== RAW SENSOR LOG ===')
for i in range(10):
    c = call_mcu(s, 'imu/count')
    qr = call_mcu(s, 'imu/qr')
    qi = call_mcu(s, 'imu/qi')
    qj = call_mcu(s, 'imu/qj')
    qk = call_mcu(s, 'imu/qk')
    print(f'Sample {i}: count={c} quat=[{qr}, {qi}, {qj}, {qk}]')
    time.sleep(0.3)
s.close()
PYEOF
python3 ~/check_motion.py
"""
child.sendline(script)
child.expect([r'=== RAW SENSOR LOG ==='], timeout=15)
child.expect([r'Sample 9:'], timeout=25)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
