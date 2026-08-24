import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=15)

child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#define BNO_USE_I2C\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <7Semi_BNO08x.h>\n'
'\n'
'static BnoI2CBus bus(Wire, -1, -1, 0x4B, 100000, -1, -1);\n'
'static BNO08x_7Semi bno(bus);\n'
'static int beginCode = -1;\n'
'static int featureCode = -1;\n'
'static int rxPackets = 0;\n'
'static float q_r = 1.0f, q_i = 0.0f, q_j = 0.0f, q_k = 0.0f;\n'
'\n'
'int getBeginCode() { return beginCode; }\n'
'int getFeatureCode() { return featureCode; }\n'
'int getRxCount() { return rxPackets; }\n'
'float getQuatR() { return q_r; }\n'
'float getQuatI() { return q_i; }\n'
'\n'
'void setup() {\n'
'  Wire.begin();\n'
'  delay(300);\n'
'  beginCode = bno.begin() ? 1 : 0;\n'
'  if (beginCode == 1) {\n'
'    featureCode = bno.enableReport(SH2_ROTATION_VECTOR, 20) ? 1 : 0;\n'
'  }\n'
'  Bridge.begin();\n'
'  Bridge.provide("getBeginCode", getBeginCode);\n'
'  Bridge.provide("getFeatureCode", getFeatureCode);\n'
'  Bridge.provide("getRxCount", getRxCount);\n'
'  Bridge.provide("getQuatR", getQuatR);\n'
'  Bridge.provide("getQuatI", getQuatI);\n'
'}\n'
'\n'
'void loop() {\n'
'  if (beginCode == 1) {\n'
'    bno.processData();\n'
'    rxPackets++;\n'
'    Quat q = bno.getQuat();\n'
'    q_r = q.r;\n'
'    q_i = q.i;\n'
'  }\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile & Upload
child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect(r'\$', timeout=15)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'\n'
'def call_rpc(method_name):\n'
'    req = msgpack.packb([0, 1, method_name, []])\n'
'    s.sendall(req)\n'
'    while True:\n'
'        buf = s.recv(1024)\n'
'        if not buf: return None\n'
'        unpacker.feed(buf)\n'
'        for msg in unpacker:\n'
'            return msg[3]\n'
'\n'
'print(\'begin() status:\', call_rpc(\'getBeginCode\'))\n'
'print(\'enableReport() status:\', call_rpc(\'getFeatureCode\'))\n'
'time.sleep(1)\n'
'print(\'rx loops executed:\', call_rpc(\'getRxCount\'))\n'
'print(\'Quat R:\', call_rpc(\'getQuatR\'))\n'
'print(\'Quat I:\', call_rpc(\'getQuatI\'))\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
