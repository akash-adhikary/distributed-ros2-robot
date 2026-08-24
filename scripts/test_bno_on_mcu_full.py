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
int imu_status = -1; // -1: init, 0: not found, 1: found 0x4B, 2: found 0x4A

int get_status() {
  return imu_status;
}

int get_qr() {
  return (int)(sensorValue.un.rotationVector.real * 10000);
}
int get_qi() {
  return (int)(sensorValue.un.rotationVector.i * 10000);
}
int get_qj() {
  return (int)(sensorValue.un.rotationVector.j * 10000);
}
int get_qk() {
  return (int)(sensorValue.un.rotationVector.k * 10000);
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/status", get_status);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);
  
  Wire.begin();
  delay(100);
  
  if (bno08x.begin_I2C(0x4B, &Wire)) {
    imu_status = 1;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else if (bno08x.begin_I2C(0x4A, &Wire)) {
    imu_status = 2;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else {
    imu_status = 0;
  }
}

void loop() {
  if (imu_status > 0) {
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
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=180)

child.sendline("exit")
child.expect(pexpect.EOF)
