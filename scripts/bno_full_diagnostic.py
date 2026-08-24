import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Create a diagnostic sketch that scans Wire, Wire1, and custom SDA/SCL pins
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'\n'
'int scanAllBuses() {\n'
'  Wire.begin();\n'
'  for (byte addr = 1; addr < 127; addr++) {\n'
'    Wire.beginTransmission(addr);\n'
'    if (Wire.endTransmission() == 0) {\n'
'      return (int)addr;\n'
'    }\n'
'  }\n'
'  #if defined(Wire1)\n'
'  Wire1.begin();\n'
'  for (byte addr = 1; addr < 127; addr++) {\n'
'    Wire1.beginTransmission(addr);\n'
'    if (Wire1.endTransmission() == 0) {\n'
'      return 0x1000 | (int)addr;\n'
'    }\n'
'  }\n'
'  #endif\n'
'  return -1;\n'
'}\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Bridge.provide("scanAll", scanAllBuses);\n'
'}\n'
'\n'
'void loop() {\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

child.sendline("sudo systemctl restart arduino-router")
idx = child.expect([r'password for arduino:', r'\$'], timeout=10)
if idx == 0:
    child.sendline("Askaban78@#")
    child.expect(r'\$', timeout=10)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(1)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'req = msgpack.packb([0, 1, \'scanAll\', []])\n'
's.sendall(req)\n'
'resp = s.recv(1024)\n'
'print(\'SCAN RESULT:\', msgpack.unpackb(resp, max_array_len=100))\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
