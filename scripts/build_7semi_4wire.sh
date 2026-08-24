#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

// Bus on Wire (address 0x4B and 0x4A) with no INT/RST constraints (-1, -1)
static BnoI2CBus bus4B(Wire, -1, -1, 0x4B, 100000, -1, -1);
static BnoI2CBus bus4A(Wire, -1, -1, 0x4A, 100000, -1, -1);
static BNO08x_7Semi imu4B(bus4B);
static BNO08x_7Semi imu4A(bus4A);

// Bus on Wire2 (Pins A4/A5 on Uno Q) with no INT/RST constraints (-1, -1)
static BnoI2CBus busW2_4B(Wire2, -1, -1, 0x4B, 100000, -1, -1);
static BnoI2CBus busW2_4A(Wire2, -1, -1, 0x4A, 100000, -1, -1);
static BNO08x_7Semi imuW2_4B(busW2_4B);
static BNO08x_7Semi imuW2_4A(busW2_4A);

static BNO08x_7Semi* active_imu = nullptr;

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
  Wire2.begin();
  delay(200);

  // Auto-detect which bus and address responds
  if (imu4B.begin()) {
    active_imu = &imu4B;
    sensor_active = 1; // Dedicated SDA/SCL (0x4B)
  } else if (imu4A.begin()) {
    active_imu = &imu4A;
    sensor_active = 2; // Dedicated SDA/SCL (0x4A)
  } else if (imuW2_4B.begin()) {
    active_imu = &imuW2_4B;
    sensor_active = 3; // A4/A5 Header (0x4B)
  } else if (imuW2_4A.begin()) {
    active_imu = &imuW2_4A;
    sensor_active = 4; // A4/A5 Header (0x4A)
  }

  if (active_imu) {
    active_imu->enableReport(GAME_ROTATION_VECTOR, 20);
  }
}

void loop() {
  if (active_imu) {
    active_imu->processData();
    float qr, qi, qj, qk;
    if (active_imu->getGameRotationVector(qi, qj, qk, qr)) {
      q_r = (int)(qr * 10000.0f);
      q_i = (int)(qi * 10000.0f);
      q_j = (int)(qj * 10000.0f);
      q_k = (int)(qk * 10000.0f);

      // Roll Pitch Yaw
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
  } else {
    // If not detected at startup, retry every loop
    if (imu4B.begin()) { active_imu = &imu4B; sensor_active = 1; active_imu->enableReport(GAME_ROTATION_VECTOR, 20); }
    else if (imu4A.begin()) { active_imu = &imu4A; sensor_active = 2; active_imu->enableReport(GAME_ROTATION_VECTOR, 20); }
    else if (imuW2_4B.begin()) { active_imu = &imuW2_4B; sensor_active = 3; active_imu->enableReport(GAME_ROTATION_VECTOR, 20); }
    else if (imuW2_4A.begin()) { active_imu = &imuW2_4A; sensor_active = 4; active_imu->enableReport(GAME_ROTATION_VECTOR, 20); }
  }

  Bridge.update();
  delay(10);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "OFFICIAL_7SEMI_DRIVER_READY"
