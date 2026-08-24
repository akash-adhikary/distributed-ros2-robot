import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""python3 -c "
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

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
print('=== LIVE SENSOR TELEMETRY TABLE ===')
print('='*80)
print(f'{\"SAMPLE\":<8} | {\"PACKETS\":<8} | {\"ROLL\":<9} | {\"PITCH\":<9} | {\"YAW\":<9} | {\"QUATERNION [w, x, y, z]\"}')
print('-'*80)

for idx in range(12):
    cnt = call_mcu(s, 'imu/count') or 0
    roll = call_mcu(s, 'imu/roll') or 0
    pitch = call_mcu(s, 'imu/pitch') or 0
    yaw = call_mcu(s, 'imu/yaw') or 0
    qr = (call_mcu(s, 'imu/qr') or 0) / 10000.0
    qi = (call_mcu(s, 'imu/qi') or 0) / 10000.0
    qj = (call_mcu(s, 'imu/qj') or 0) / 10000.0
    qk = (call_mcu(s, 'imu/qk') or 0) / 10000.0
    
    print(f'#{idx+1:05d}   | {cnt:<8d} | {roll:+4d} deg  | {pitch:+4d} deg  | {yaw:+4d} deg  | [{qr:+.3f}, {qi:+.3f}, {qj:+.3f}, {qk:+.3f}]')
    time.sleep(0.25)
print('='*80)
s.close()
"
""")
child.expect([r'=== LIVE SENSOR TELEMETRY TABLE ==='], timeout=15)
child.expect([r'#00012'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
