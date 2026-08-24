#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, -1, -1);
static BNO08x_7Semi bno(bus);

struct ImuData {
  float ax, ay, az;
  float gx, gy, gz;
  float mx, my, mz;
  float qi, qj, qk, qr;
  float lax, lay, laz;
};
ImuData d;

int q_r = 10000, q_i = 0, q_j = 0, q_k = 0;
int roll_deg = 0, pitch_deg = 0, yaw_deg = 0;
int ax_mg = 0, ay_mg = 0, az_mg = 1000;
int gx_mdps = 0, gy_mdps = 0, gz_mdps = 0;
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
int get_ax() { return ax_mg; }
int get_ay() { return ay_mg; }
int get_az() { return az_mg; }
int get_gx() { return gx_mdps; }
int get_gy() { return gy_mdps; }
int get_gz() { return gz_mdps; }

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
  Bridge.provide("imu/ax", get_ax);
  Bridge.provide("imu/ay", get_ay);
  Bridge.provide("imu/az", get_az);
  Bridge.provide("imu/gx", get_gx);
  Bridge.provide("imu/gy", get_gy);
  Bridge.provide("imu/gz", get_gz);

  Wire2.begin();
  delay(100);

  if (bno.begin()) {
    sensor_active = 1;
    bno.enableAcc(20);
    bno.enableGyro(20);
    bno.enableRotationVector(20);
    bno.enableGameRotationVector(20);
  }
}

void loop() {
  if (sensor_active == 1) {
    bno.processData();

    if (bno.getQuaternion(d.qi, d.qj, d.qk, d.qr) || bno.getGameRotationVector(d.qi, d.qj, d.qk, d.qr)) {
      q_r = (int)(d.qr * 10000.0f);
      q_i = (int)(d.qi * 10000.0f);
      q_j = (int)(d.qj * 10000.0f);
      q_k = (int)(d.qk * 10000.0f);

      // Roll Pitch Yaw
      float sinr_cosp = 2.0f * (d.qr * d.qi + d.qj * d.qk);
      float cosr_cosp = 1.0f - 2.0f * (d.qi * d.qi + d.qj * d.qj);
      float roll = atan2(sinr_cosp, cosr_cosp) * 180.0f / 3.14159265f;

      float sinp = 2.0f * (d.qr * d.qj - d.qk * d.qi);
      float pitch;
      if (fabs(sinp) >= 1.0f) pitch = copysign(90.0f, sinp);
      else pitch = asin(sinp) * 180.0f / 3.14159265f;

      float siny_cosp = 2.0f * (d.qr * d.qk + d.qi * d.qj);
      float cosy_cosp = 1.0f - 2.0f * (d.qj * d.qj + d.qk * d.qk);
      float yaw = atan2(siny_cosp, cosy_cosp) * 180.0f / 3.14159265f;

      roll_deg = (int)roll;
      pitch_deg = (int)pitch;
      yaw_deg = (int)yaw;
      packet_count++;
    }

    if (bno.getAccelerometer(d.ax, d.ay, d.az)) {
      ax_mg = (int)(d.ax * 100.0f);
      ay_mg = (int)(d.ay * 100.0f);
      az_mg = (int)(d.az * 100.0f);
    }
    if (bno.getGyroscope(d.gx, d.gy, d.gz)) {
      gx_mdps = (int)(d.gx * 1000.0f);
      gy_mdps = (int)(d.gy * 1000.0f);
      gz_mdps = (int)(d.gz * 1000.0f);
    }
  } else {
    if (bno.begin()) {
      sensor_active = 1;
      bno.enableAcc(20);
      bno.enableGyro(20);
      bno.enableRotationVector(20);
      bno.enableGameRotationVector(20);
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
echo "PRODUCTION_IMU_READY"
