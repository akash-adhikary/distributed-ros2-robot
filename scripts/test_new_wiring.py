import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'PYEOF' > ~/check_act.py
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
print('Active code:', call_mcu(s, 'imu/active'))
print('Count:', call_mcu(s, 'imu/count'))
print('Roll:', call_mcu(s, 'imu/roll'))
print('Pitch:', call_mcu(s, 'imu/pitch'))
print('Yaw:', call_mcu(s, 'imu/yaw'))
s.close()
PYEOF
python3 ~/check_act.py
""")
child.expect([r'Active code:'], timeout=15)
child.expect([r'Yaw:'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
