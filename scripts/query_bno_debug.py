import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'req = msgpack.packb([0, 1, \'scanI2C\', []])\n'
's.sendall(req)\n'
'resp = bytearray()\n'
'while True:\n'
'    chunk = s.recv(1024)\n'
'    if not chunk: break\n'
'    resp.extend(chunk)\n'
'    try:\n'
'        data = msgpack.unpackb(resp, max_array_len=100)\n'
'        print(\'SUCCESSFULLY RECEIVED RPC:\', data)\n'
'        break\n'
'    except Exception as e:\n'
'        pass\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
