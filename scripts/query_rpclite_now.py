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
'            data = msgpack.unpackb(buf, max_array_len=100)\n'
'            return data[3]\n'
'        except Exception:\n'
'            pass\n'
'\n'
'print(\'BNO08x Initialized State (1=Success, 0=Failed):\', call(\'getStatus\'))\n'
'for i in range(5):\n'
'    w = call(\'getQW\')\n'
'    x = call(\'getQX\')\n'
'    y = call(\'getQY\')\n'
'    z = call(\'getQZ\')\n'
'    gz = call(\'getGZ\')\n'
'    print(f\'Sample {i+1} -> Quat: (w={w:.4f}, x={x:.4f}, y={y:.4f}, z={z:.4f}) | GyroZ={gz:.4f}\')\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
