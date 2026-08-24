import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

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
'  delay(2000);\n'
'  Serial1.println("DEBUG_START");\n'
'  Wire.begin();\n'
'  delay(500);\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    Serial1.println("DEBUG_BNO_OK");\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bnoOk = true;\n'
'  } else {\n'
'    Serial1.println("DEBUG_BNO_FAIL");\n'
'  }\n'
'}\n'
'\n'
'void loop() {\n'
'  if (!bnoOk) {\n'
'    Serial1.println("DEBUG_NO_SENSOR");\n'
'    delay(1000);\n'
'    return;\n'
'  }\n'
'  if (bno08x.getSensorEvent(&sensorValue)) {\n'
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
'  } else {\n'
'    Serial1.println("DEBUG_NO_DATA");\n'
'  }\n'
'  delay(100);\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl stop arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Reset Zephyr to make it run setup() again while we are listening
child.sendline("sudo /usr/bin/gpioset -c /dev/gpiochip1 -t0 37=0")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import serial, time, threading, os\n'
'ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'print(\'=== READING DEBUG STREAM ===\')\n'
'def release_reset():\n'
'    time.sleep(0.5)\n'
'    os.system(\'sudo /usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1\')\n'
'threading.Thread(target=release_reset).start()\n'
'start = time.time()\n'
'count = 0\n'
'while time.time() - start < 8 and count < 15:\n'
'    try:\n'
'        line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'        if line:\n'
'            print(\'UART:\', line)\n'
'            count += 1\n'
'    except Exception as e:\n'
'        print(e)\n'
'ser.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
