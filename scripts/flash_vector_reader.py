import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Write clean Bridge firmware with basic vector returns
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <SparkFun_BNO08x_Arduino_Library.h>\n'
'\n'
'BNO08x myIMU;\n'
'\n'
'std::vector<float> readQuat() {\n'
'  std::vector<float> data(7, 0.0f);\n'
'  data[3] = 1.0f;\n'
'  if (myIMU.dataAvailable()) {\n'
'    data[0] = myIMU.getQuatI();\n'
'    data[1] = myIMU.getQuatJ();\n'
'    data[2] = myIMU.getQuatK();\n'
'    data[3] = myIMU.getQuatReal();\n'
'    data[4] = myIMU.getGyroX();\n'
'    data[5] = myIMU.getGyroY();\n'
'    data[6] = myIMU.getGyroZ();\n'
'  }\n'
'  return data;\n'
'}\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  myIMU.begin(0x4B, Wire);\n'
'  myIMU.enableRotationVector(20);\n'
'  myIMU.enableGyro(20);\n'
'  Bridge.begin();\n'
'  Bridge.provide("readQuat", readQuat);\n'
'}\n'
'\n'
'void loop() {\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile & Upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

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
'for i in range(5):\n'
'    req = msgpack.packb([0, i+1, \'readQuat\', []])\n'
'    s.sendall(req)\n'
'    got = False\n'
'    while not got:\n'
'        buf = s.recv(1024)\n'
'        if not buf: break\n'
'        unpacker.feed(buf)\n'
'        for msg in unpacker:\n'
'            print(f\'SAMPLE {i+1} DATA:\', msg)\n'
'            got = True\n'
'            break\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
