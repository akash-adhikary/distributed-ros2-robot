#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, -1, -1);
static BNO08x_7Semi bno(bus);

int q_r = 10000, q_i = 0, q_j = 0, q_k = 0;
int roll_deg = 0, pitch_deg = 0, yaw_deg = 0;
int sensor_active = 0;
int packet_count = 0;
int raw_rx_bytes = 0;

int get_active() { return sensor_active; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }
int get_qj() { return q_j; }
int get_qk() { return q_k; }
int get_roll() { return roll_deg; }
int get_pitch() { return pitch_deg; }
int get_yaw() { return yaw_deg; }
int get_count() { return packet_count; }
int get_raw() { return raw_rx_bytes; }

void send_soft_reset() {
  uint8_t reset_cmd[5] = {5, 0, 1, 0, 1}; // SHTP Executable Reset command
  Wire2.beginTransmission(0x4B);
  Wire2.write(reset_cmd, 5);
  Wire2.endTransmission();
}

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
  Bridge.provide("imu/raw", get_raw);

  Wire2.begin();
  delay(100);

  send_soft_reset();
  delay(300);

  if (bno.begin()) {
    sensor_active = 1;
    bno.enableRotationVector(20);
    bno.enableAcc(20);
  }
}

void loop() {
  if (sensor_active == 1) {
    uint8_t buf[64];
    int n = bno.readPacket(buf, sizeof(buf));
    if (n > 0) {
      raw_rx_bytes += n;
      bno.processPacket(buf, n);
      float qi, qj, qk, qr;
      if (bno.getQuaternion(qi, qj, qk, qr)) {
        q_r = (int)(qr * 10000.0f);
        q_i = (int)(qi * 10000.0f);
        q_j = (int)(qj * 10000.0f);
        q_k = (int)(qk * 10000.0f);

        float sinr_cosp = 2.0f * (qr * qi + qj * qk);
        float cosr_cosp = 1.0f - 2.0f * (qi * qi + qj * qj);
        roll_deg = (int)(atan2(sinr_cosp, cosr_cosp) * 180.0f / 3.14159265f);

        float sinp = 2.0f * (qr * qj - qk * qi);
        if (fabs(sinp) >= 1.0f) pitch_deg = (int)copysign(90.0f, sinp);
        else pitch_deg = (int)(asin(sinp) * 180.0f / 3.14159265f);

        float siny_cosp = 2.0f * (qr * qk + qi * qj);
        float cosy_cosp = 1.0f - 2.0f * (qj * qj + qk * qk);
        yaw_deg = (int)(atan2(siny_cosp, cosy_cosp) * 180.0f / 3.14159265f);
        packet_count++;
      }
    }
  }

  Bridge.update();
  delay(10);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "SOFT_RESET_READY"
