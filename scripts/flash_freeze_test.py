import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>

Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;
bool bnoOk = false;
String bnoStatus = "NOT_STARTED";

String get_status() {
    return bnoStatus;
}

String get_imu() {
    if (!bnoOk) return "BNO_NOT_OK";
    if (bno08x.getSensorEvent(&sensorValue)) {
        if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {
            return String(sensorValue.un.rotationVector.real, 4) + "," +
                   String(sensorValue.un.rotationVector.i, 4) + "," +
                   String(sensorValue.un.rotationVector.j, 4) + "," +
                   String(sensorValue.un.rotationVector.k, 4);
        }
    }
    return "NO_DATA";
}

void setup() {
  Bridge.begin();
  Bridge.provide("get_status", get_status);
  Bridge.provide("get_imu", get_imu);
  
  bnoStatus = "BRIDGE_STARTED";
  
  Wire.begin();
  bnoStatus = "WIRE_STARTED";
  delay(100);
  
  if (bno08x.begin_I2C(0x4B, &Wire)) {
    bnoStatus = "BNO_OK";
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
    bnoOk = true;
  } else {
    bnoStatus = "BNO_FAIL";
  }
}

void loop() {
  Bridge.update();
  delay(10);
}
SKETCH

echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 3
cat << "PY" > ~/query_status.py
import socket, msgpack, time
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/var/run/arduino-router.sock')
    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)
    req = msgpack.packb([0, 1, "get_status", []])
    s.sendall(req)
    print("=== SENT REQ ===")
    start = time.time()
    while time.time() - start < 3:
        s.settimeout(1)
        try:
            buf = s.recv(1024)
            if not buf: break
            unpacker.feed(buf)
            for msg in unpacker:
                print("RECV:", msg)
        except socket.timeout:
            pass
except Exception as e:
    print("Err:", e)
finally:
    s.close()
PY
echo "Running query..."
python3 ~/query_status.py
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=200)

child.sendline("exit")
child.expect(pexpect.EOF)
