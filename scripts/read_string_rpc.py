import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(1)\n'
'try:\n'
'    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
'    s.connect(\'/var/run/arduino-router.sock\')\n'
'    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'    print(\'=== READING STRING NOTIFY VIA BRIDGE ===\')\n'
'    start = time.time()\n'
'    count = 0\n'
'    while time.time() - start < 10 and count < 10:\n'
'        s.settimeout(1)\n'
'        try:\n'
'            buf = s.recv(1024)\n'
'            if not buf: break\n'
'            unpacker.feed(buf)\n'
'            for msg in unpacker:\n'
'                print(\'RECV:\', msg)\n'
'                count += 1\n'
'        except socket.timeout:\n'
'            pass\n'
'except Exception as e:\n'
'    print(\'Err:\', e)\n'
'finally:\n'
'    s.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
