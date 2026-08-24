#!/usr/bin/env python3
"""
Probe: Query Uno Q STM32 Bridge Directly over Unix Domain Socket
Usage: python3 query_raw_bridge.py
"""
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

print('=== QUERYING MCU BRIDGE (imu/raw) ===')
for i in range(10):
    s.sendall(msgpack.packb([0, 1, 'imu/raw', []]))
    buf = s.recv(512)
    u = msgpack.Unpacker()
    u.feed(buf)
    for m in u:
        print(f'Sample #{i+1:02d} -> {m[3]}')
    time.sleep(0.1)
s.close()
"
""")
child.expect([r'Sample #10'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
