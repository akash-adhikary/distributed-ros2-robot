import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Write pure Wire I2C scanner sketch (no external dependencies)
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Wire.h>\n'
'\n'
'void setup() {\n'
'  Serial.begin(115200);\n'
'  Wire.begin();\n'
'  delay(1500);\n'
'  Serial.println("--- MCU I2C SCANNER START ---");\n'
'}\n'
'\n'
'void loop() {\n'
'  byte error, address;\n'
'  int nDevices = 0;\n'
'  Serial.println("Scanning...");\n'
'  for(address = 1; address < 127; address++ ) {\n'
'    Wire.beginTransmission(address);\n'
'    error = Wire.endTransmission();\n'
'    if (error == 0) {\n'
'      Serial.print("I2C device found at address 0x");\n'
'      if (address < 16) Serial.print("0");\n'
'      Serial.print(address, HEX);\n'
'      Serial.println(" !");\n'
'      nDevices++;\n'
'    }\n'
'  }\n'
'  if (nDevices == 0) Serial.println("No I2C devices found\\n");\n'
'  else Serial.println("done\\n");\n'
'  delay(3000);\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=60)

# Upload
child.sendline("arduino-cli upload -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
