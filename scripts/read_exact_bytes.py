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

print('=== EXACT INCOMING SHTP FRAME BYTES FROM SENSOR ===')
for i in range(10):
    tot = call_mcu('f/tot')
    flen = call_mcu('f/len')
    bytes_arr = [call_mcu(f'f/b{j}') for j in range(14)]
    hex_str = ' '.join([f'{b:02X}' if b is not None else '??' for b in bytes_arr])
    print(f'Sample #{i+1:02d} | TotalFrames={tot} | Len={flen} | RawBytes: [ {hex_str} ]')
    time.sleep(0.3)
s.close()
"
""")
child.expect([r'=== EXACT INCOMING SHTP FRAME BYTES FROM SENSOR ==='], timeout=15)
child.expect([r'Sample #10'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
