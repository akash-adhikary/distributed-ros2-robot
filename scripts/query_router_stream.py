import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
's.sendall(msgpack.packb([0, 1, \'getStatus\', []]))\n'
'buf = bytearray()\n'
'while True:\n'
'    b = s.recv(1024)\n'
'    if not b: break\n'
'    buf.extend(b)\n'
'    try:\n'
'        obj = msgpack.unpackb(buf, max_array_len=100)\n'
'        print(\'COMPLETE RPC OBJECT:\', obj)\n'
'        break\n'
'    except Exception:\n'
'        pass\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
