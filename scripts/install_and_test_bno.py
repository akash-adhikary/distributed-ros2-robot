import pexpect, sys
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Install official 7Semi BNO08x library
child.sendline('arduino-cli lib install "7Semi BNO08x"')
child.expect(r'\$', timeout=30)

# Create a small sketch to scan I2C and read BNO08x via Wire
child.sendline('mkdir -p ~/BnoTest && cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Wire.h>\n'
'#include <7Semi_BNO08x.h>\n'
'\n'
'BNO08x imu;\n'
'\n'
'void setup() {\n'
'  Serial.begin(115200);\n'
'  Wire.begin();\n'
'  delay(2000);\n'
'  Serial.println("[MCU] Starting BNO08x I2C Test...");\n'
'  \n'
'  // Scan I2C on MCU Wire\n'
'  Serial.println("[MCU] Scanning I2C bus on headers...");\n'
'  int nDevices = 0;\n'
'  for (byte address = 1; address < 127; address++) {\n'
'    Wire.beginTransmission(address);\n'
'    byte error = Wire.endTransmission();\n'
'    if (error == 0) {\n'
'      Serial.print("[MCU] I2C device found at 0x");\n'
'      if (address < 16) Serial.print("0");\n'
'      Serial.println(address, HEX);\n'
'      nDevices++;\n'
'    }\n'
'  }\n'
'  if (nDevices == 0) Serial.println("[MCU] No I2C devices found on headers.");\n'
'}\n'
'\n'
'void loop() {\n'
'  delay(1000);\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile sketch for Uno Q MCU
child.sendline('arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest')
child.expect(r'\$', timeout=60)

child.sendline("exit")
child.expect(pexpect.EOF)
