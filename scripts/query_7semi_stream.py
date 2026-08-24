import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=10)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'\n'
'def call_rpc(method_name):\n'
'    req = msgpack.packb([0, 1, method_name, []])\n'
'    s.sendall(req)\n'
'    while True:\n'
'        buf = s.recv(1024)\n'
'        if not buf: return None\n'
'        unpacker.feed(buf)\n'
'        for msg in unpacker:\n'
'            return msg[3]\n'
'\n'
'print(\'7Semi Driver Initialized:\', call_rpc(\'getInitStatus\'))\n'
'for i in range(10):\n'
'    qr = call_rpc(\'getQuatReal\')\n'
'    qi = call_rpc(\'getQuatI\')\n'
'    qj = call_rpc(\'getQuatJ\')\n'
'    qk = call_rpc(\'getQuatK\')\n'
'    gz = call_rpc(\'getGyroZ\')\n'
'    print(f\'Sample {i+1}: Quat(w={qr:.4f}, x={qi:.4f}, y={qj:.4f}, z={qk:.4f}) | GyroZ={gz:.4f}\')\n'
'    time.sleep(0.2)\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
