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

t0 = time.time()
count = 0
for _ in range(200):
    s.sendall(msgpack.packb([0, 1, 'imu/raw', []]))
    buf = s.recv(1024)
    count += 1
dt = time.time() - t0
print(f'200 queries took {dt:.3f}s -> {count/dt:.1f} Hz (Ultra Fast!)')
s.close()
"
""")
child.expect([r'Ultra Fast'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
