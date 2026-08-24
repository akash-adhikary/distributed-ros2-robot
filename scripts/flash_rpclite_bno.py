import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RPClite.h>\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'SerialTransport transport(Serial1);\n'
'RPCServer server(transport);\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'float qw = 1.0f, qx = 0.0f, qy = 0.0f, qz = 0.0f, gz = 0.0f;\n'
'bool bnoOk = false;\n'
'\n'
'float getQW() { return qw; }\n'
'float getQX() { return qx; }\n'
'float getQY() { return qy; }\n'
'float getQZ() { return qz; }\n'
'float getGZ() { return gz; }\n'
'int getStatus() { return bnoOk ? 1 : 0; }\n'
'\n'
'void setup() {\n'
'  Serial1.begin(115200);\n'
'  Wire.begin();\n'
'  delay(200);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'    bnoOk = true;\n'
'  }\n'
'  server.bind("getQW", getQW);\n'
'  server.bind("getQX", getQX);\n'
'  server.bind("getQY", getQY);\n'
'  server.bind("getQZ", getQZ);\n'
'  server.bind("getGZ", getGZ);\n'
'  server.bind("getStatus", getStatus);\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bnoOk && bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      qw = sensorValue.un.rotationVector.real;\n'
'      qx = sensorValue.un.rotationVector.i;\n'
'      qy = sensorValue.un.rotationVector.j;\n'
'      qz = sensorValue.un.rotationVector.k;\n'
'    } else if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {\n'
'      gz = sensorValue.un.gyroscope.z;\n'
'    }\n'
'  }\n'
'  server.run();\n'
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
'\n'
'def call(fn):\n'
'    s.sendall(msgpack.packb([0, 1, fn, []]))\n'
'    buf = bytearray()\n'
'    while True:\n'
'        b = s.recv(1024)\n'
'        if not b: return None\n'
'        buf.extend(b)\n'
'        try:\n'
'            data = msgpack.unpackb(buf, max_array_len=100)\n'
'            return data[3]\n'
'        except Exception:\n'
'            pass\n'
'\n'
'print(\'BNO08x Initialized State (1=Success, 0=Failed):\', call(\'getStatus\'))\n'
'for i in range(5):\n'
'    w = call(\'getQW\')\n'
'    x = call(\'getQX\')\n'
'    y = call(\'getQY\')\n'
'    z = call(\'getQZ\')\n'
'    gz = call(\'getGZ\')\n'
'    print(f\'Sample {i+1} -> Quat(w={w:.4f}, x={x:.4f}, y={y:.4f}, z={z:.4f}) | GyroZ={gz:.4f}\')\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
