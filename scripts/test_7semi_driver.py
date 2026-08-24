import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

sketch_code = """cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include "7Semi_BNO08x.h"

BnoI2CBus bnoBus4B(Wire, -1, -1, 0x4B, 100000, -1, -1);
BNO08x_7Semi imu(bnoBus4B);

int q_r = 10000, q_i = 0, q_j = 0, q_k = 0;
int roll_deg = 0, pitch_deg = 0, yaw_deg = 0;
int sensor_active = 0;
int packet_count = 0;

int get_active() { return sensor_active; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }
int get_qj() { return q_j; }
int get_qk() { return q_k; }
int get_roll() { return roll_deg; }
int get_pitch() { return pitch_deg; }
int get_yaw() { return yaw_deg; }
int get_count() { return packet_count; }

void setup() {
  Bridge.begin();
  Bridge.provide("imu/active", get_active);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);
  Bridge.provide("imu/roll", get_roll);
  Bridge.provide("imu/pitch", get_pitch);
  Bridge.provide("imu/yaw", get_yaw);
  Bridge.provide("imu/count", get_count);

  Wire.begin();
  delay(100);

  if (imu.begin()) {
    sensor_active = 1;
    imu.enableReport(GAME_ROTATION_VECTOR, 20000); // 50 Hz
  }
}

void loop() {
  if (sensor_active) {
    imu.processData();
    const State &st = imu.getState();
    if (st.hasGameQuat) {
      q_r = (int)(st.grv_q.r * 10000.0f);
      q_i = (int)(st.grv_q.i * 10000.0f);
      q_j = (int)(st.grv_q.j * 10000.0f);
      q_k = (int)(st.grv_q.k * 10000.0f);

      // Roll Pitch Yaw
      float qr = st.grv_q.r;
      float qi = st.grv_q.i;
      float qj = st.grv_q.j;
      float qk = st.grv_q.k;

      float sinr_cosp = 2.0f * (qr * qi + qj * qk);
      float cosr_cosp = 1.0f - 2.0f * (qi * qi + qj * qj);
      float roll = atan2(sinr_cosp, cosr_cosp) * 180.0f / 3.14159265f;

      float sinp = 2.0f * (qr * qj - qk * qi);
      float pitch;
      if (fabs(sinp) >= 1.0f) pitch = copysign(90.0f, sinp);
      else pitch = asin(sinp) * 180.0f / 3.14159265f;

      float siny_cosp = 2.0f * (qr * qk + qi * qj);
      float cosy_cosp = 1.0f - 2.0f * (qj * qj + qk * qk);
      float yaw = atan2(siny_cosp, cosy_cosp) * 180.0f / 3.14159265f;

      roll_deg = (int)roll;
      pitch_deg = (int)pitch;
      yaw_deg = (int)yaw;
      packet_count++;
    }
  }
  Bridge.update();
  delay(10);
}
SKETCH

echo "Compiling 7Semi BNO08x sketch..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading 7Semi BNO08x sketch..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "7SEMI_READY"
"""
child.sendline(sketch_code)
child.expect([r'7SEMI_READY'], timeout=120)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
