import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""python3 -c "
import socket, msgpack, time

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')

def call_mcu(m):
    try:
        s.sendall(msgpack.packb([0, 1, m, []]))
        time.sleep(0.01)
        buf = s.recv(1024)
        u = msgpack.Unpacker()
        u.feed(buf)
        for msg in u: return msg[3]
    except: pass
    return None

print('=== LIVE VERIFIED BNO086 SAMPLES (WITH INT D2 & BUFFER DRAIN) ===')
for i in range(12):
    frames = call_mcu('imu/frames')
    cnt = call_mcu('imu/count')
    roll = call_mcu('imu/roll')
    pitch = call_mcu('imu/pitch')
    yaw = call_mcu('imu/yaw')
    qr = call_mcu('imu/qr')
    qi = call_mcu('imu/qi')
    qj = call_mcu('imu/qj')
    qk = call_mcu('imu/qk')
    ax = call_mcu('imu/ax')
    ay = call_mcu('imu/ay')
    az = call_mcu('imu/az')
    gx = call_mcu('imu/gx')
    gy = call_mcu('imu/gy')
    gz = call_mcu('imu/gz')
    
    print(f'Sample #{i+1:02d} | Frames={frames} | RotationPackets={cnt} | Roll={roll}° Pitch={pitch}° Yaw={yaw}° | Quat=[{qr/10000.0:.3f}, {qi/10000.0:.3f}, {qj/10000.0:.3f}, {qk/10000.0:.3f}] | Acc=[{ax/100.0:.2f}, {ay/100.0:.2f}, {az/100.0:.2f}] m/s²')
    time.sleep(0.25)
s.close()
"
""")
child.expect([r'=== LIVE VERIFIED BNO086 SAMPLES (WITH INT D2 & BUFFER DRAIN) ==='], timeout=15)
child.expect([r'Sample #12'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
