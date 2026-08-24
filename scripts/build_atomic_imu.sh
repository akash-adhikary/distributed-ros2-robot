#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, 2, -1);
static BNO08x_7Semi bno(bus);

int16_t imu_packet[10] = {10000, 0, 0, 0, 0, 0, 0, 0, 0, 0};
int packet_count = 0;

int get_pkt_val(int idx) {
  if (idx >= 0 && idx < 10) return (int)imu_packet[idx];
  return 0;
}

int get_count() { return packet_count; }

void setup() {
  Bridge.begin();
  Bridge.provide("imu/p0", []() { return get_pkt_val(0); }); // qr
  Bridge.provide("imu/p1", []() { return get_pkt_val(1); }); // qi
  Bridge.provide("imu/p2", []() { return get_pkt_val(2); }); // qj
  Bridge.provide("imu/p3", []() { return get_pkt_val(3); }); // qk
  Bridge.provide("imu/p4", []() { return get_pkt_val(4); }); // lax (cm/s^2)
  Bridge.provide("imu/p5", []() { return get_pkt_val(5); }); // lay (cm/s^2)
  Bridge.provide("imu/p6", []() { return get_pkt_val(6); }); // laz (cm/s^2)
  Bridge.provide("imu/p7", []() { return get_pkt_val(7); }); // gx (mdps)
  Bridge.provide("imu/p8", []() { return get_pkt_val(8); }); // gy (mdps)
  Bridge.provide("imu/p9", []() { return get_pkt_val(9); }); // gz (mdps)
  Bridge.provide("imu/count", get_count);

  Wire2.begin();
  pinMode(2, INPUT_PULLUP);
  delay(100);

  bno.begin();
  delay(50);
  bno.enableRotationVector(10);     // 100 Hz
  bno.enableGameRotationVector(10); // 100 Hz
  bno.enableLinearAccel(10);        // 100 Hz Linear Acceleration (Gravity Free!)
  bno.enableGyro(10);               // 100 Hz Gyroscope
}

void loop() {
  uint8_t buf[128];
  int n = bno.readPacket(buf, sizeof(buf));
  if (n > 0) {
    bno.processPacket(buf, n);

    float qi = 0, qj = 0, qk = 0, qr = 1.0;
    float lax = 0, lay = 0, laz = 0;
    float gx = 0, gy = 0, gz = 0;

    bool has_quat = bno.getQuaternion(qi, qj, qk, qr) || bno.getGameRotationVector(qi, qj, qk, qr);
    bool has_lin = bno.getLinearAccel(lax, lay, laz);
    bool has_gyro = bno.getGyroscope(gx, gy, gz);

    if (has_quat) {
      imu_packet[0] = (int16_t)(qr * 10000.0f);
      imu_packet[1] = (int16_t)(qi * 10000.0f);
      imu_packet[2] = (int16_t)(qj * 10000.0f);
      imu_packet[3] = (int16_t)(qk * 10000.0f);
      packet_count++;
    }

    if (has_lin) {
      imu_packet[4] = (int16_t)(lax * 100.0f);
      imu_packet[5] = (int16_t)(lay * 100.0f);
      imu_packet[6] = (int16_t)(laz * 100.0f);
    }

    if (has_gyro) {
      imu_packet[7] = (int16_t)(gx * 1000.0f);
      imu_packet[8] = (int16_t)(gy * 1000.0f);
      imu_packet[9] = (int16_t)(gz * 1000.0f);
    }
  }

  Bridge.update();
  delay(2);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "ATOMIC_IMU_READY"
