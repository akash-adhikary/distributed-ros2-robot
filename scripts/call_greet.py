import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline('cat << "PY" > ~/call_greet.py\n'
'import socket, msgpack, time\n'
'try:\n'
'    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
'    s.connect(\'/var/run/arduino-router.sock\')\n'
'    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'    req = msgpack.packb([0, 1, "greet", []])\n'
'    s.sendall(req)\n'
'    print("=== SENT REQ ===")\n'
'    start = time.time()\n'
'    while time.time() - start < 3:\n'
'        s.settimeout(1)\n'
'        try:\n'
'            buf = s.recv(1024)\n'
'            if not buf: break\n'
'            unpacker.feed(buf)\n'
'            for msg in unpacker:\n'
'                print("RECV:", msg)\n'
'        except socket.timeout:\n'
'            pass\n'
'except Exception as e:\n'
'    print("Err:", e)\n'
'finally:\n'
'    s.close()\n'
'PY\n')
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 ~/call_greet.py && echo QUERY_DONE")
child.expect([r'QUERY_DONE'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
