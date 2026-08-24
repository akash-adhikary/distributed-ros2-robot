import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'\n'
'int scanResult = -1;\n'
'\n'
'int doScan() {\n'
'  Wire.begin();\n'
'  for (byte addr = 1; addr < 127; addr++) {\n'
'    Wire.beginTransmission(addr);\n'
'    if (Wire.endTransmission() == 0) {\n'
'      return addr;\n'
'    }\n'
'  }\n'
'  return -1;\n'
'}\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Monitor.begin(115200);\n'
'  scanResult = doScan();\n'
'}\n'
'\n'
'void loop() {\n'
'  Monitor.print("SCAN_ADDR=");\n'
'  Monitor.println(scanResult);\n'
'  delay(500);\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Read Monitor logs
child.sendline("journalctl -u arduino-router.service -n 15 --no-pager")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
