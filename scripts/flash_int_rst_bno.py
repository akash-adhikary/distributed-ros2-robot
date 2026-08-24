import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=15)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'float qw = 1.0f, qx = 0.0f, qy = 0.0f, qz = 0.0f;\n'
'int status = -1;\n'
'\n'
'float getQW() { return qw; }\n'
'float getQX() { return qx; }\n'
'float getQY() { return qy; }\n'
'float getQZ() { return qz; }\n'
'int getStatus() { return status; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  delay(200);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    status = 1;\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'  } else {\n'
'    status = 0;\n'
'  }\n'
'  Bridge.begin();\n'
'  Bridge.provide("getQW", getQW);\n'
'  Bridge.provide("getQX", getQX);\n'
'  Bridge.provide("getQY", getQY);\n'
'  Bridge.provide("getQZ", getQZ);\n'
'  Bridge.provide("getStatus", getStatus);\n'
'}\n'
'\n'
'void loop() {\n'
'  if (status == 1 && bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      qw = sensorValue.un.rotationVector.real;\n'
'      qx = sensorValue.un.rotationVector.i;\n'
'      qy = sensorValue.un.rotationVector.j;\n'
'      qz = sensorValue.un.rotationVector.k;\n'
'    }\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'for fn in [\'getStatus\', \'getQW\', \'getQX\', \'getQY\', \'getQZ\']:\n'
'    s.sendall(msgpack.packb([0, 1, fn, []]))\n'
'    buf = bytearray()\n'
'    while True:\n'
'        b = s.recv(1024)\n'
'        if not b: break\n'
'        buf.extend(b)\n'
'        try:\n'
'            data = msgpack.unpackb(buf, max_array_len=100)\n'
'            print(f\'{fn} ->\', data[3])\n'
'            break\n'
'        except Exception:\n'
'            pass\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
