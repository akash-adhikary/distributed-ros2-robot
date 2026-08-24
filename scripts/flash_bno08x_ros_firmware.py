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
int bno_ready = 0;

int get_ready() { return bno_ready; }
int get_qr() { return (int)(sensorValue.un.rotationVector.real * 10000); }
int get_qi() { return (int)(sensorValue.un.rotationVector.i * 10000); }
int get_qj() { return (int)(sensorValue.un.rotationVector.j * 10000); }
int get_qk() { return (int)(sensorValue.un.rotationVector.k * 10000); }
int get_ax() { return (int)(sensorValue.un.accelerometer.x * 1000); }
int get_ay() { return (int)(sensorValue.un.accelerometer.y * 1000); }
int get_az() { return (int)(sensorValue.un.accelerometer.z * 1000); }
int get_gx() { return (int)(sensorValue.un.gyroscope.x * 1000); }
int get_gy() { return (int)(sensorValue.un.gyroscope.y * 1000); }
int get_gz() { return (int)(sensorValue.un.gyroscope.z * 1000); }

void setup() {
  Bridge.begin();
  Bridge.provide("imu/ready", get_ready);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);
  Bridge.provide("imu/ax", get_ax);
  Bridge.provide("imu/ay", get_ay);
  Bridge.provide("imu/az", get_az);
  Bridge.provide("imu/gx", get_gx);
  Bridge.provide("imu/gy", get_gy);
  Bridge.provide("imu/gz", get_gz);
  
  Wire.begin();
  delay(100);
  
  if (bno08x.begin_I2C(0x4B, &Wire)) {
    bno_ready = 1;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
    bno08x.enableReport(SH2_ACCELEROMETER, 20000);
    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);
  }
}

void loop() {
  if (bno_ready) {
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

cat << "PY" > ~/read_imu_live.py
import socket, msgpack, time

def call_mcu(s, method):
    req = msgpack.packb([0, 1, method, []])
    s.sendall(req)
    time.sleep(0.02)
    buf = s.recv(1024)
    unpacker = msgpack.Unpacker()
    unpacker.feed(buf)
    for msg in unpacker:
        return msg[3]
    return None

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
ready = call_mcu(s, "imu/ready")
print(f"IMU READY: {ready}")
if ready:
    for _ in range(5):
        qr = call_mcu(s, "imu/qr") / 10000.0 if call_mcu(s, "imu/qr") is not None else 0
        qi = call_mcu(s, "imu/qi") / 10000.0 if call_mcu(s, "imu/qi") is not None else 0
        qj = call_mcu(s, "imu/qj") / 10000.0 if call_mcu(s, "imu/qj") is not None else 0
        qk = call_mcu(s, "imu/qk") / 10000.0 if call_mcu(s, "imu/qk") is not None else 0
        print(f"Quaternion [r, i, j, k]: [{qr:.4f}, {qi:.4f}, {qj:.4f}, {qk:.4f}]")
        time.sleep(0.2)
s.close()
PY

python3 ~/read_imu_live.py
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
