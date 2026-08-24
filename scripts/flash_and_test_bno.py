import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("bash ~/run_shtp.sh")
child.expect([r'ALL_DONE'], timeout=120)
child.expect([r'\$ '], timeout=15)

test_cmd = """cat << 'PYEOF' > ~/test_live_quat.py
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
print('ACTIVE:', call_mcu(s, 'imu/active'))
print('COUNT:', call_mcu(s, 'imu/count'))
for _ in range(5):
    print('QUAT:', call_mcu(s, 'imu/qr'), call_mcu(s, 'imu/qi'), call_mcu(s, 'imu/qj'), call_mcu(s, 'imu/qk'))
    time.sleep(0.2)
s.close()
PYEOF
python3 ~/test_live_quat.py
"""
child.sendline(test_cmd)
child.expect([r'\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
