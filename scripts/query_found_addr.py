import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'PYEOF' > ~/check_addr.py
import socket, msgpack
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
s.sendall(msgpack.packb([0, 1, 'i2c/found', []]))
buf = s.recv(1024)
u = msgpack.Unpacker()
u.feed(buf)
for m in u: print('FOUND ADDR:', hex(m[3] if m[3] is not None else 0))
s.close()
PYEOF
python3 ~/check_addr.py
""")
child.expect([r'FOUND ADDR:'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
