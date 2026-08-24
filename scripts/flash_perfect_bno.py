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
'float q_r = 1.0f, q_i = 0.0f, q_j = 0.0f, q_k = 0.0f, gz = 0.0f;\n'
'bool bnoReady = false;\n'
'\n'
'float get_qr() { return q_r; }\n'
'float get_qi() { return q_i; }\n'
'float get_qj() { return q_j; }\n'
'float get_qk() { return q_k; }\n'
'float get_gz() { return gz; }\n'
'int get_status() { return bnoReady ? 1 : 0; }\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'    bnoReady = true;\n'
'  }\n'
'  Bridge.provide("get_qr", get_qr);\n'
'  Bridge.provide("get_qi", get_qi);\n'
'  Bridge.provide("get_qj", get_qj);\n'
'  Bridge.provide("get_qk", get_qk);\n'
'  Bridge.provide("get_gz", get_gz);\n'
'  Bridge.provide("get_status", get_status);\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bnoReady && bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      q_r = sensorValue.un.rotationVector.real;\n'
'      q_i = sensorValue.un.rotationVector.i;\n'
'      q_j = sensorValue.un.rotationVector.j;\n'
'      q_k = sensorValue.un.rotationVector.k;\n'
'    } else if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {\n'
'      gz = sensorValue.un.gyroscope.z;\n'
'    }\n'
'  }\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Query live values using pure msgpack-rpc
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
'            return msgpack.unpackb(buf, max_array_len=100)[3]\n'
'        except Exception:\n'
'            pass\n'
'\n'
'print(\'BNO08x Initialized:\', call(\'get_status\'))\n'
'for i in range(10):\n'
'    qr = call(\'get_qr\')\n'
'    qi = call(\'get_qi\')\n'
'    qj = call(\'get_qj\')\n'
'    qk = call(\'get_qk\')\n'
'    gz = call(\'get_gz\')\n'
'    print(f\'Sample {i+1} -> Orientation: (w={qr:.4f}, x={qi:.4f}, y={qj:.4f}, z={qk:.4f}) | GyroZ={gz:.4f}\')\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
