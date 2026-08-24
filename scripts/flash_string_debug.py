import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

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
'  Wire.begin();\n'
'  delay(1000);\n'
'  Bridge.notify("DBG", "Starting BNO");\n'
'  if (bno08x.begin_I2C(0x4B, &Wire)) {\n'
'    Bridge.notify("DBG", "BNO Begin Success");\n'
'    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);\n'
'    bnoOk = true;\n'
'  } else {\n'
'    Bridge.notify("DBG", "BNO Begin Failed");\n'
'  }\n'
'}\n'
'\n'
'void loop() {\n'
'  if (!bnoOk) {\n'
'    Bridge.notify("DBG", "No BNO, waiting...");\n'
'    Bridge.update();\n'
'    delay(1000);\n'
'    return;\n'
'  }\n'
'  if (bno08x.getSensorEvent(&sensorValue)) {\n'
'    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {\n'
'      String s = String(sensorValue.un.rotationVector.real, 4) + "," +\n'
'                 String(sensorValue.un.rotationVector.i, 4) + "," +\n'
'                 String(sensorValue.un.rotationVector.j, 4) + "," +\n'
'                 String(sensorValue.un.rotationVector.k, 4);\n'
'      Bridge.notify("Q", s);\n'
'    }\n'
'  } else {\n'
'    Bridge.notify("DBG", "No event");\n'
'  }\n'
'  Bridge.update();\n'
'  delay(100);\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

# Re-run python read to see debug
child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(1)\n'
'try:\n'
'    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
'    s.connect(\'/var/run/arduino-router.sock\')\n'
'    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'    print(\'=== READING DEBUG VIA BRIDGE ===\')\n'
'    start = time.time()\n'
'    count = 0\n'
'    while time.time() - start < 15 and count < 20:\n'
'        s.settimeout(1)\n'
'        try:\n'
'            buf = s.recv(1024)\n'
'            if not buf: break\n'
'            unpacker.feed(buf)\n'
'            for msg in unpacker:\n'
'                print(\'RECV:\', msg)\n'
'                count += 1\n'
'        except socket.timeout:\n'
'            pass\n'
'except Exception as e:\n'
'    print(\'Err:\', e)\n'
'finally:\n'
'    s.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
