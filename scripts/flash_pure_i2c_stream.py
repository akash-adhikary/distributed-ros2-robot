import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'\n'
'int testPing() {\n'
'  return 42;\n'
'}\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Bridge.provide("testPing", testPing);\n'
'}\n'
'\n'
'void loop() {\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Compile & Upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
's.sendall(msgpack.packb([0, 1, \'testPing\', []]))\n'
'buf = bytearray()\n'
'while True:\n'
'    b = s.recv(1024)\n'
'    if not b: break\n'
'    buf.extend(b)\n'
'    try:\n'
'        print(\'PING RESPONSE:\', msgpack.unpackb(buf, max_array_len=100))\n'
'        break\n'
'    except Exception:\n'
'        pass\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
