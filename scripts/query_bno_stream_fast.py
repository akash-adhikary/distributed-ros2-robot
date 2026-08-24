import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'for i in range(5):\n'
'    req = msgpack.packb([0, i+1, \'getIMUData\', []])\n'
'    s.sendall(req)\n'
'    resp = s.recv(1024)\n'
'    data = msgpack.unpackb(resp, max_array_len=100)\n'
'    print(f\'READ SUCCESS {i+1}:\', data)\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
