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

act = call_mcu('imu/active')
cnt = call_mcu('imu/count')
r = call_mcu('imu/roll')
p = call_mcu('imu/pitch')
y = call_mcu('imu/yaw')
qr = call_mcu('imu/qr')
qi = call_mcu('imu/qi')
qj = call_mcu('imu/qj')
qk = call_mcu('imu/qk')
ax = call_mcu('imu/ax')
ay = call_mcu('imu/ay')
az = call_mcu('imu/az')

print('================ HARDWARE TEST SUMMARY ================')
print(f'Sensor Active: {act}')
print(f'Sensor Packet Count: {cnt}')
print(f'Attitude (Roll/Pitch/Yaw): {r}°, {p}°, {y}°')
print(f'Quaternion [w,x,y,z]: [{qr}, {qi}, {qj}, {qk}]')
print(f'Raw Accelerometer: [{ax}, {ay}, {az}]')
print('=======================================================')
s.close()
"
""")
child.expect([r'======================================================='], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
