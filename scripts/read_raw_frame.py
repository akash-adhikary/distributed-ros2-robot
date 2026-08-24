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

print('=== RAW SHTP FRAMES RECEIVED OVER WIRE2 ===')
for i in range(10):
    tot = call_mcu('raw/tot')
    length = call_mcu('raw/len')
    chan = call_mcu('raw/chan')
    rep = call_mcu('raw/rep')
    d0 = call_mcu('raw/d0')
    d1 = call_mcu('raw/d1')
    d2 = call_mcu('raw/d2')
    d3 = call_mcu('raw/d3')
    d4 = call_mcu('raw/d4')
    d5 = call_mcu('raw/d5')
    print(f'Frame #{i+1:02d} | TotalFrames={tot} | Len={length} | Channel={chan} | ReportID=0x{rep:02X} | Bytes=[{d0}, {d1}, {d2}, {d3}, {d4}, {d5}]')
    time.sleep(0.25)
s.close()
"
""")
child.expect([r'=== RAW SHTP FRAMES RECEIVED OVER WIRE2 ==='], timeout=15)
child.expect([r'Frame #10'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
