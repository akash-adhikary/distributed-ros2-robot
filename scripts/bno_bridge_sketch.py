import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Create an RPC-enabled sketch that uses Arduino_RPClite to publish I2C status cleanly to Linux
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'\n'
'int foundAddress = -1;\n'
'\n'
'int scanI2C() {\n'
'  Wire.begin();\n'
'  for (byte addr = 1; addr < 127; addr++) {\n'
'    Wire.beginTransmission(addr);\n'
'    if (Wire.endTransmission() == 0) {\n'
'      return (int)addr;\n'
'    }\n'
'  }\n'
'  return -1;\n'
'}\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Bridge.provide("scanI2C", scanI2C);\n'
'}\n'
'\n'
'void loop() {\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile and upload
child.sendline("arduino-cli compile -v --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=180)

child.sendline("exit")
child.expect(pexpect.EOF)
