import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Stop arduino-router so we have exclusive raw ownership of /dev/ttyHS1
child.sendline("echo 'Askaban78@#' | sudo -S systemctl stop arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Reset and take STM32 out of reset using the exact hardware GPIO pins from 10-imola.conf
child.sendline("/usr/bin/gpioset -c /dev/gpiochip1 -t0 37=0")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)
child.sendline("/usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Flash clean BNO08x UART streamer sketch
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
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
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
'    }\n'
'  }\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

# Release GPIO reset line to run sketch
child.sendline("/usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Read live stream directly from /dev/ttyHS1
child.sendline('python3 -c "\n'
'import serial, time\n'
'ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'print(\'=== READING LIVE BNO08X ORIENTATION STREAM FROM ttyHS1 ===\')\n'
'start = time.time()\n'
'count = 0\n'
'while time.time() - start < 5 and count < 10:\n'
'    line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'    if line.startswith(\'Q,\'):\n'
'        parts = line.split(\',\')\n'
'        print(f\'Sample {count+1} -> Quat(w={parts[1]}, x={parts[2]}, y={parts[3]}, z={parts[4]})\')\n'
'        count += 1\n'
'ser.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
