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
'print(\'--- LISTENING FOR REAL-TIME SENSOR STREAM FROM STM32 ---\')\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'count = 0\n'
'start = time.time()\n'
'while time.time() - start < 5 and count < 10:\n'
'    buf = s.recv(1024)\n'
'    if not buf: break\n'
'    unpacker.feed(buf)\n'
'    for msg in unpacker:\n'
'        print(\'STREAMED SENSOR REPORT:\', msg)\n'
'        if isinstance(msg, list) and len(msg) >= 2 and msg[0] == 0:\n'
'            s.sendall(msgpack.packb([1, msg[1], None, True]))\n'
'        count += 1\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
