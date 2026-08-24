import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Write simple float getters
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <SparkFun_BNO08x_Arduino_Library.h>\n'
'\n'
'BNO08x myIMU;\n'
'\n'
'float getQuatI() { return myIMU.dataAvailable() ? myIMU.getQuatI() : 0.0f; }\n'
'float getQuatJ() { return myIMU.getQuatJ(); }\n'
'float getQuatK() { return myIMU.getQuatK(); }\n'
'float getQuatReal() { return myIMU.getQuatReal(); }\n'
'float getGyroZ() { return myIMU.getGyroZ(); }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  myIMU.begin(0x4B, Wire);\n'
'  myIMU.enableRotationVector(20);\n'
'  myIMU.enableGyro(20);\n'
'  Bridge.begin();\n'
'  Bridge.provide("getQuatI", getQuatI);\n'
'  Bridge.provide("getQuatJ", getQuatJ);\n'
'  Bridge.provide("getQuatK", getQuatK);\n'
'  Bridge.provide("getQuatReal", getQuatReal);\n'
'  Bridge.provide("getGyroZ", getGyroZ);\n'
'}\n'
'\n'
'void loop() {\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

# Upload
child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=60)

# Restart router
child.sendline("sudo systemctl restart arduino-router")
idx = child.expect([r'password for arduino:', r'\$'], timeout=10)
if idx == 0:
    child.sendline("Askaban78@#")
    child.expect(r'\$', timeout=10)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'for fn in [\'getQuatReal\', \'getQuatI\', \'getQuatJ\', \'getQuatK\', \'getGyroZ\']:\n'
'    req = msgpack.packb([0, 1, fn, []])\n'
'    s.sendall(req)\n'
'    got = False\n'
'    while not got:\n'
'        buf = s.recv(1024)\n'
'        if not buf: break\n'
'        unpacker.feed(buf)\n'
'        for msg in unpacker:\n'
'            print(f\'{fn} ->\', msg)\n'
'            got = True\n'
'            break\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
