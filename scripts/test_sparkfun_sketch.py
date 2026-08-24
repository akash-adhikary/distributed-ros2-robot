import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

sketch = """
cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <SparkFun_BNO08x_Arduino_Library.h>

BNO08x myIMU;

int q_r = 10000;
int q_i = 0;
int q_j = 0;
int q_k = 0;
int sensor_active = 0;

int get_active() { return sensor_active; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }
int get_qj() { return q_j; }
int get_qk() { return q_k; }

void setup() {
  Bridge.begin();
  Bridge.provide("imu/active", get_active);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);

  Wire.begin();
  if (myIMU.begin(0x4B, Wire)) {
    sensor_active = 1;
    myIMU.enableGameRotationVector(20); // 50 Hz (20ms)
  }
}

void loop() {
  if (sensor_active) {
    if (myIMU.wasReset()) {
      myIMU.enableGameRotationVector(20);
    }
    if (myIMU.getReadings()) {
      if (myIMU.getSensorEventID() == SENSOR_REPORTID_GAME_ROTATION_VECTOR) {
        q_r = (int)(myIMU.getGameQuatReal() * 10000.0f);
        q_i = (int)(myIMU.getGameQuatI() * 10000.0f);
        q_j = (int)(myIMU.getGameQuatJ() * 10000.0f);
        q_k = (int)(myIMU.getGameQuatK() * 10000.0f);
      }
    }
  }
  Bridge.update();
  delay(5);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
"""
child.sendline(sketch)
child.expect([r'arduino@blissy:\~\$ '], timeout=45)

child.sendline("exit")
child.expect(pexpect.EOF)
