import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Write sketch using official 7Semi_BNO08x library that matches the hardware
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <7Semi_BNO08x.h>\n'
'\n'
'BNO08x_I2C imu(&Wire, 0x4B);\n'
'bool bnoActive = false;\n'
'float q_r = 1.0f, q_i = 0.0f, q_j = 0.0f, q_k = 0.0f, gz = 0.0f;\n'
'\n'
'float getQuatReal() { return q_r; }\n'
'float getQuatI() { return q_i; }\n'
'float getQuatJ() { return q_j; }\n'
'float getQuatK() { return q_k; }\n'
'float getGyroZ() { return gz; }\n'
'int getInitStatus() { return bnoActive ? 1 : 0; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  if (imu.begin()) {\n'
'    imu.enableRotationVector(20);\n'
'    imu.enableGyro(20);\n'
'    bnoActive = true;\n'
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
'  if (bnoActive && imu.dataAvailable()) {\n'
'    q_r = imu.getQuatReal();\n'
'    q_i = imu.getQuatI();\n'
'    q_j = imu.getQuatJ();\n'
'    q_k = imu.getQuatK();\n'
'    gz = imu.getGyroZ();\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

child.sendline("cat /home/arduino/Arduino/libraries/7Semi_BNO08x/src/7Semi_BNO08x.h | head -n 35")
child.expect(r'\$', timeout=10)

child.sendline("exit")
child.expect(pexpect.EOF)
