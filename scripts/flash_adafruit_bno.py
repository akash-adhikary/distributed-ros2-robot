import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Install Adafruit BNO08x library which has complete sh2_SensorValue_t reporting
child.sendline('arduino-cli lib install "Adafruit BNO08x"')
child.expect(r'\$', timeout=60)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'\n'
'float getQuatI() { return sensorValue.un.rotationVector.i; }\n'
'float getQuatJ() { return sensorValue.un.rotationVector.j; }\n'
'float getQuatK() { return sensorValue.un.rotationVector.k; }\n'
'float getQuatReal() { return sensorValue.un.rotationVector.real; }\n'
'float getGyroZ() { return sensorValue.un.gyroscope.z; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  bno08x.begin_I2C(0x4B, &Wire);\n'
'  bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'  bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'  Bridge.begin();\n'
'  Bridge.provide("getQuatI", getQuatI);\n'
'  Bridge.provide("getQuatJ", getQuatJ);\n'
'  Bridge.provide("getQuatK", getQuatK);\n'
'  Bridge.provide("getQuatReal", getQuatReal);\n'
'  Bridge.provide("getGyroZ", getGyroZ);\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bno08x.wasReset()) {\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'  }\n'
'  bno08x.getSensorEvent(&sensorValue);\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile & Upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=180)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

# Query orientation values
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
child.expect(r'\$', timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
