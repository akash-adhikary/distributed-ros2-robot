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
's.settimeout(2.0)\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'try:\n'
'    for _ in range(10):\n'
'        buf = s.recv(1024)\n'
'        if not buf: break\n'
'        unpacker.feed(buf)\n'
'        for msg in unpacker:\n'
'            print(\'GOT NOTIFY:\', msg)\n'
'except Exception as e:\n'
'    print(\'Finished / Timeout:\', e)\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
