import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'def call(fn):\n'
'    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
'    s.connect(\'/var/run/arduino-router.sock\')\n'
'    s.sendall(msgpack.packb([0, 1, fn, []]))\n'
'    resp = s.recv(1024)\n'
'    s.close()\n'
'    return msgpack.unpackb(resp, max_array_len=100)[3]\n'
'\n'
'print(\'beginCode:\', call(\'getBeginCode\'))\n'
'print(\'featureCode:\', call(\'getFeatureCode\'))\n'
'print(\'rxCount:\', call(\'getRxCount\'))\n'
'print(\'quatR:\', call(\'getQuatR\'))\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
