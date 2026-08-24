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

print('=== PIN D2 STATE OVER TIME ===')
for i in range(10):
    val = call_mcu('pin/d2')
    print(f'Sample #{i+1:02d}: Pin D2 Logic Level = {val}')
    time.sleep(0.2)
s.close()
"
""")
child.expect([r'=== PIN D2 STATE OVER TIME ==='], timeout=15)
child.expect([r'Sample #10'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
