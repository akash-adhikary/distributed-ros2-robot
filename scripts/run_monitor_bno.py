import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'PYEOF' > ~/monitor_bno.py
import socket, msgpack, time, sys

def call_mcu(s, m):
    try:
        s.sendall(msgpack.packb([0, 1, m, []]))
        time.sleep(0.01)
        buf = s.recv(1024)
        u = msgpack.Unpacker()
        u.feed(buf)
        for msg in u: return msg[3]
    except Exception:
        pass
    return None

try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/var/run/arduino-router.sock')
    print('Connected to Uno Q MCU. Tilt/Move sensor now to observe values:')
    print('-'*70)

    for i in range(12):
        act = call_mcu(s, 'imu/active')
        cnt = call_mcu(s, 'imu/count')
        roll = call_mcu(s, 'imu/roll') or 0
        pitch = call_mcu(s, 'imu/pitch') or 0
        yaw = call_mcu(s, 'imu/yaw') or 0
        qr = (call_mcu(s, 'imu/qr') or 0) / 10000.0
        qi = (call_mcu(s, 'imu/qi') or 0) / 10000.0
        qj = (call_mcu(s, 'imu/qj') or 0) / 10000.0
        qk = (call_mcu(s, 'imu/qk') or 0) / 10000.0
        print(f'[{i:02d}] Active={act} | Samples={cnt} | Roll={roll:4d} deg | Pitch={pitch:4d} deg | Yaw={yaw:4d} deg | Quat=[{qr:+.2f}, {qi:+.2f}, {qj:+.2f}, {qk:+.2f}]')
        time.sleep(0.3)
    s.close()
except Exception as e:
    print('Error:', e)
PYEOF
python3 ~/monitor_bno.py
""")
child.expect([r'\[11\] Active='], timeout=25)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
