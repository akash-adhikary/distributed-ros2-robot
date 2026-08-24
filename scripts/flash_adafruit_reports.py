import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Write sketch using standard Adafruit_BNO08x SH2 report loop and status check
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'float q_real = 1.0, q_i = 0.0, q_j = 0.0, q_k = 0.0, gz = 0.0;\n'
'bool bnoInitialized = false;\n'
'\n'
'float getQuatReal() { return q_real; }\n'
'float getQuatI() { return q_i; }\n'
'float getQuatJ() { return q_j; }\n'
'float getQuatK() { return q_k; }\n'
'float getGyroZ() { return gz; }\n'
'int getInitStatus() { return bnoInitialized ? 1 : 0; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  delay(100);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'    bnoInitialized = true;\n'
'  }\n'
'  Bridge.begin();\n'
'  Bridge.provide("getQuatReal", getQuatReal);\n'
'  Bridge.provide("getQuatI", getQuatI);\n'
'  Bridge.provide("getQuatJ", getQuatJ);\n'
'  Bridge.provide("getQuatK", getQuatK);\n'
'  Bridge.provide("getGyroZ", getGyroZ);\n'
'  Bridge.provide("getInitStatus", getInitStatus);\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bnoInitialized) {\n'
'    while (bno08x.getSensorEvent(&sensorValue)) {\n'
'      if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'        q_real = sensorValue.un.rotationVector.real;\n'
'        q_i = sensorValue.un.rotationVector.i;\n'
'        q_j = sensorValue.un.rotationVector.j;\n'
'        q_k = sensorValue.un.rotationVector.k;\n'
'      } else if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {\n'
'        gz = sensorValue.un.gyroscope.z;\n'
'      }\n'
'    }\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=180)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
