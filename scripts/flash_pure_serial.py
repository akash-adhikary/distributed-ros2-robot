import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Check all serial/tty devices and permissions
child.sendline("echo 'Askaban78@#' | sudo -S systemctl stop arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Create a direct high-speed binary UART firmware on Serial1 (STM32 to Qualcomm ttyHS1 link)
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'bool bnoOk = false;\n'
'\n'
'void setup() {\n'
'  Serial1.begin(115200);\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 10000); // 100Hz\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 10000);\n'
'    bnoOk = true;\n'
'  }\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bnoOk && bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      Serial1.print("Q,");\n'
'      Serial1.print(sensorValue.un.rotationVector.real, 4);\n'
'      Serial1.print(",");\n'
'      Serial1.print(sensorValue.un.rotationVector.i, 4);\n'
'      Serial1.print(",");\n'
'      Serial1.print(sensorValue.un.rotationVector.j, 4);\n'
'      Serial1.print(",");\n'
'      Serial1.println(sensorValue.un.rotationVector.k, 4);\n'
'    } else if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {\n'
'      Serial1.print("G,");\n'
'      Serial1.print(sensorValue.un.gyroscope.x, 4);\n'
'      Serial1.print(",");\n'
'      Serial1.print(sensorValue.un.gyroscope.y, 4);\n'
'      Serial1.print(",");\n'
'      Serial1.println(sensorValue.un.gyroscope.z, 4);\n'
'    }\n'
'  }\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Compile & upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

# Read raw stream from /dev/ttyHS1 (direct STM32 UART link)
child.sendline('python3 -c "\n'
'import serial, time\n'
'ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=2)\n'
'print(\'CONNECTED TO DIRECT MCU SERIAL (ttyHS1)\')\n'
'for i in range(15):\n'
'    line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'    if line:\n'
'        print(\'RAW IMU STREAM ->\', line)\n'
'ser.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
