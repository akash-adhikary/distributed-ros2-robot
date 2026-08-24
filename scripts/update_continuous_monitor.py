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
    print('Connected to Uno Q MCU. Tilt/Rotate the BNO08x sensor:')
    print('='*75)
    print(f'{"SAMPLE":<8} | {"ACTIVE":<7} | {"SAMPLES":<8} | {"ROLL":<9} | {"PITCH":<9} | {"YAW":<9} | {"QUATERNION [w, x, y, z]"}')
    print('-'*75)

    idx = 0
    while True:
        act = call_mcu(s, 'imu/active')
        cnt = call_mcu(s, 'imu/count') or 0
        roll = call_mcu(s, 'imu/roll') or 0
        pitch = call_mcu(s, 'imu/pitch') or 0
        yaw = call_mcu(s, 'imu/yaw') or 0
        qr = (call_mcu(s, 'imu/qr') or 0) / 10000.0
        qi = (call_mcu(s, 'imu/qi') or 0) / 10000.0
        qj = (call_mcu(s, 'imu/qj') or 0) / 10000.0
        qk = (call_mcu(s, 'imu/qk') or 0) / 10000.0
        
        status_str = "YES" if act == 1 else "NO"
        print(f'#{idx:05d}   | {status_str:<7} | {cnt:<8d} | {roll:+4d} deg  | {pitch:+4d} deg  | {yaw:+4d} deg  | [{qr:+.3f}, {qi:+.3f}, {qj:+.3f}, {qk:+.3f}]', end='\\r')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
except KeyboardInterrupt:
    print('\\nExiting monitor.')
except Exception as e:
    print('\\nError connecting:', e)
finally:
    try: s.close()
    except: pass
PYEOF
""")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
