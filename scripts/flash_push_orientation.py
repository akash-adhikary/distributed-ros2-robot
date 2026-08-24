import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'bool bnoReady = false;\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000); // 50Hz\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'    bnoReady = true;\n'
'  }\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bnoReady && bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      float qw = sensorValue.un.rotationVector.real;\n'
'      float qx = sensorValue.un.rotationVector.i;\n'
'      float qy = sensorValue.un.rotationVector.j;\n'
'      float qz = sensorValue.un.rotationVector.k;\n'
'      Bridge.call("on_quat", qw, qx, qy, qz);\n'
'    } else if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {\n'
'      float gx = sensorValue.un.gyroscope.x;\n'
'      float gy = sensorValue.un.gyroscope.y;\n'
'      float gz = sensorValue.un.gyroscope.z;\n'
'      Bridge.call("on_gyro", gx, gy, gz);\n'
'    }\n'
'  }\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Compile & Upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Run Python server on Linux that receives Bridge.call pushes
child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'print(\'LISTENING FOR MCU SENSOR PUSH EVENTS ON ROUTER BRIDGE...\')\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'count = 0\n'
'start = time.time()\n'
'while time.time() - start < 6 and count < 15:\n'
'    buf = s.recv(1024)\n'
'    if not buf: break\n'
'    unpacker.feed(buf)\n'
'    for msg in unpacker:\n'
'        print(\'RECEIVED SENSOR EVENT ->\', msg)\n'
'        # Respond with RPC success: [1 (RESPONSE), msg_id, None, True]\n'
'        if isinstance(msg, list) and len(msg) >= 2 and msg[0] == 0:\n'
'            s.sendall(msgpack.packb([1, msg[1], None, True]))\n'
'        count += 1\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
