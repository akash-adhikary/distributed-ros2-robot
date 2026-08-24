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
int bno_code = 0;

int get_code() { return bno_code; }

void setup() {
  Bridge.begin();
  Bridge.provide("imu/code", get_code);
  
  Wire.begin();
  delay(100);
  
  // Try 0x4B
  if (bno08x.begin_I2C(0x4B, &Wire)) {
    bno_code = 1;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else if (bno08x.begin_I2C(0x4A, &Wire)) {
    bno_code = 2;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else {
    // Check raw Wire transmission
    Wire.beginTransmission(0x4B);
    byte err4b = Wire.endTransmission();
    Wire.beginTransmission(0x4A);
    byte err4a = Wire.endTransmission();
    bno_code = 100 + (err4b * 10) + err4a;
  }
}

void loop() {
  if (bno_code == 1 || bno_code == 2) {
    bno08x.getSensorEvent(&sensorValue);
  }
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

cat << "PY" > ~/read_bno_code.py
import socket, msgpack, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
req = msgpack.packb([0, 1, "imu/code", []])
s.sendall(req)
time.sleep(0.05)
buf = s.recv(1024)
unpacker = msgpack.Unpacker()
unpacker.feed(buf)
for msg in unpacker:
    print("BNO_INIT_CODE:", msg[3])
s.close()
PY

python3 ~/read_bno_code.py
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=180)

child.sendline("exit")
child.expect(pexpect.EOF)
