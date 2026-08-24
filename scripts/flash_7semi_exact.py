import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Write exact sketch matching 7Semi official driver example
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#define BNO_USE_I2C\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <7Semi_BNO08x.h>\n'
'\n'
'static BnoI2CBus bus(Wire, -1, -1, 0x4B, 100000, -1, -1);\n'
'static BNO08x_7Semi bno(bus);\n'
'static bool initialized = false;\n'
'\n'
'static float q_r = 1.0f, q_i = 0.0f, q_j = 0.0f, q_k = 0.0f, gz = 0.0f;\n'
'\n'
'float getQuatReal() { return q_r; }\n'
'float getQuatI() { return q_i; }\n'
'float getQuatJ() { return q_j; }\n'
'float getQuatK() { return q_k; }\n'
'float getGyroZ() { return gz; }\n'
'int getInitStatus() { return initialized ? 1 : 0; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  if (bno.begin()) {\n'
'    bno.enableReport(SH2_ROTATION_VECTOR, 20);\n'
'    bno.enableReport(SH2_GYROSCOPE_CALIBRATED, 20);\n'
'    initialized = true;\n'
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
'  if (initialized) {\n'
'    bno.processData();\n'
'    Quat q = bno.getQuat();\n'
'    Vec3 g = bno.getGyro();\n'
'    q_r = q.r;\n'
'    q_i = q.i;\n'
'    q_j = q.j;\n'
'    q_k = q.k;\n'
'    gz = g.z;\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile & Upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
