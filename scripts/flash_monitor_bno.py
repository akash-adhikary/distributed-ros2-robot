import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Restart router
child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Use Monitor.println (official RouterBridge monitor)
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <Adafruit_BNO08x.h>\n'
'\n'
'Adafruit_BNO08x bno08x;\n'
'sh2_SensorValue_t sensorValue;\n'
'bool bnoOk = false;\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Monitor.begin(115200);\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  Monitor.println("--- BNO08X STARTUP ---");\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    Monitor.println("BNO08X FOUND ON I2C 0x4B!");\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);\n'
'    bnoOk = true;\n'
'  } else {\n'
'    Monitor.println("BNO08X NOT FOUND ON 0x4B");\n'
'  }\n'
'}\n'
'\n'
'void loop() {\n'
'  if (bnoOk && bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      Monitor.print("Q,");\n'
'      Monitor.print(sensorValue.un.rotationVector.real, 4);\n'
'      Monitor.print(",");\n'
'      Monitor.print(sensorValue.un.rotationVector.i, 4);\n'
'      Monitor.print(",");\n'
'      Monitor.print(sensorValue.un.rotationVector.j, 4);\n'
'      Monitor.print(",");\n'
'      Monitor.println(sensorValue.un.rotationVector.k, 4);\n'
'    }\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

# Check journal logs of router to view Monitor.println stream
child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router && sleep 3 && journalctl -u arduino-router.service -n 30 --no-pager")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
