#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, 2, -1);
static BNO08x_7Semi bno(bus);

float qi = 0, qj = 0, qk = 0, qr = 1.0;
float ax = 0, ay = 0, az = 9.81;
float gx = 0, gy = 0, gz = 0;
int roll_deg = 0, pitch_deg = 0, yaw_deg = 0;
int q_r = 10000, q_i = 0, q_j = 0, q_k = 0;
int packet_count = 0;
int rx_frames = 0;

String imu_str = "10000,0,0,0,0,0,981,0,0,0,0";

void setup() {
  Bridge.begin();
  Bridge.provide("imu/raw", []() { return imu_str; });
  Bridge.provide("imu/count", []() { return packet_count; });

  Wire2.begin();
  pinMode(2, INPUT_PULLUP);
  delay(100);

  bno.begin();
  delay(50);
  bno.enableAcc(20);
  bno.enableGyro(20);
  bno.enableRotationVector(20);
  bno.enableGameRotationVector(20);
}

void loop() {
  uint8_t buf[128];
  int n = bno.readPacket(buf, sizeof(buf));
  if (n > 0) {
    rx_frames++;
    bno.processPacket(buf, n);

    bool updated = false;
    if (bno.getQuaternion(qi, qj, qk, qr)) updated = true;
    else if (bno.getGameRotationVector(qi, qj, qk, qr)) updated = true;

    if (updated) {
      q_r = (int)(qr * 10000.0f);
      q_i = (int)(qi * 10000.0f);
      q_j = (int)(qj * 10000.0f);
      q_k = (int)(qk * 10000.0f);

      // Roll Pitch Yaw
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

    bno.getAccelerometer(ax, ay, az);
    bno.getGyroscope(gx, gy, gz);

    // Format: qr,qi,qj,qk,ax,ay,az,gx,gy,gz,count
    imu_str = String(q_r) + "," + String(q_i) + "," + String(q_j) + "," + String(q_k) + "," +
              String((int)(ax * 100.0f)) + "," + String((int)(ay * 100.0f)) + "," + String((int)(az * 100.0f)) + "," +
              String((int)(gx * 1000.0f)) + "," + String((int)(gy * 1000.0f)) + "," + String((int)(gz * 1000.0f)) + "," +
              String(packet_count);
  }

  Bridge.update();
  delay(2);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "ROCKSOLID_IMU_READY"
