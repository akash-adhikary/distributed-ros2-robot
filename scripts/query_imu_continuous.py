import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline('cat << "PY" > ~/query_loop.py\n'
'import socket, msgpack, time\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'req = msgpack.packb([0, 1, "imu/status", []])\n'
's.sendall(req)\n'
'time.sleep(0.1)\n'
'buf = s.recv(1024)\n'
'unpacker.feed(buf)\n'
'for msg in unpacker:\n'
'    print("FOUND_ADDR_HEX:", hex(msg[3]) if msg[3] else "NONE")\n'
's.close()\n'
'PY\n')
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 ~/query_loop.py")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
