import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <SparkFun_BNO080_Arduino_Library.h>\n'
'\n'
'BNO080 myIMU;\n'
'bool bnoReady = false;\n'
'\n'
'float q_r = 1.0, q_i = 0.0, q_j = 0.0, q_k = 0.0, gz = 0.0;\n'
'\n'
'float getQuatReal() { return q_r; }\n'
'float getQuatI() { return q_i; }\n'
'float getQuatJ() { return q_j; }\n'
'float getQuatK() { return q_k; }\n'
'float getGyroZ() { return gz; }\n'
'int getInitStatus() { return bnoReady ? 1 : 0; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  delay(200);\n'
'  if (myIMU.begin(0x4B, Wire)) {\n'
'    Wire.setClock(400000);\n'
'    myIMU.enableRotationVector(20);\n'
'    myIMU.enableGyro(20);\n'
'    bnoReady = true;\n'
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
'  if (bnoReady && myIMU.dataAvailable()) {\n'
'    q_r = myIMU.getQuatReal();\n'
'    q_i = myIMU.getQuatI();\n'
'    q_j = myIMU.getQuatJ();\n'
'    q_k = myIMU.getQuatK();\n'
'    gz = myIMU.getGyroZ();\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
