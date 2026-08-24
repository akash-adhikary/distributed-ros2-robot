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

print('=== LIVE SHTP SAMPLES FROM BNO086 ===')
for i in range(12):
    length = call_mcu('imu/len')
    cnt = call_mcu('imu/cnt')
    roll = call_mcu('imu/roll')
    pitch = call_mcu('imu/pitch')
    yaw = call_mcu('imu/yaw')
    qr = call_mcu('imu/qr')
    qi = call_mcu('imu/qi')
    print(f'Sample #{i+1:02d} | Packets: {cnt} | PacketLen: {length} | Roll: {roll}° | Pitch: {pitch}° | Yaw: {yaw}° | Quat: [{qr}, {qi}]')
    time.sleep(0.3)
s.close()
"
""")
child.expect([r'=== LIVE SHTP SAMPLES FROM BNO086 ==='], timeout=15)
child.expect([r'Sample #12'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
