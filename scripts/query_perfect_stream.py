import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'\n'
'def call(fn):\n'
'    s.sendall(msgpack.packb([0, 1, fn, []]))\n'
'    buf = bytearray()\n'
'    while True:\n'
'        b = s.recv(1024)\n'
'        if not b: return None\n'
'        buf.extend(b)\n'
'        try:\n'
'            return msgpack.unpackb(buf, max_array_len=100)[3]\n'
'        except Exception:\n'
'            pass\n'
'\n'
'print(\'BNO08x Initialized State:\', call(\'get_status\'))\n'
'for i in range(10):\n'
'    qr = call(\'get_qr\')\n'
'    qi = call(\'get_qi\')\n'
'    qj = call(\'get_qj\')\n'
'    qk = call(\'get_qk\')\n'
'    gz = call(\'get_gz\')\n'
'    print(f\'Sample {i+1} -> Orientation: (w={qr:.4f}, x={qi:.4f}, y={qj:.4f}, z={qk:.4f}) | GyroZ={gz:.4f}\')\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
