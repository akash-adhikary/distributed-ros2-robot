import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

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
'print(\'begin() return code:\', call_rpc(\'getBeginCode\'))\n'
'print(\'enableReport() return code:\', call_rpc(\'getFeatureCode\'))\n'
'print(\'Quat R (w):\', call_rpc(\'getQuatR\'))\n'
'print(\'Quat I (x):\', call_rpc(\'getQuatI\'))\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
