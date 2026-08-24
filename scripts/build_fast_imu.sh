#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, 2, -1);
static BNO08x_7Semi bno(bus);

String imu_data_str = "10000,0,0,0,0,0,0,0,0,0";

void setup() {
  Bridge.begin();
  Bridge.provide("imu/raw", []() { return imu_data_str; });

  Wire2.begin();
  pinMode(2, INPUT_PULLUP);
  delay(100);

  bno.begin();
  delay(50);
  bno.enableRotationVector(10);     // 100 Hz
  bno.enableGameRotationVector(10); // 100 Hz
  bno.enableLinearAccel(10);        // 100 Hz
  bno.enableGyro(10);               // 100 Hz
}

void loop() {
  uint8_t buf[128];
  int n = bno.readPacket(buf, sizeof(buf));
  if (n > 0) {
    bno.processPacket(buf, n);

    float qi = 0, qj = 0, qk = 0, qr = 1.0;
    float lax = 0, lay = 0, laz = 0;
    float gx = 0, gy = 0, gz = 0;

    bno.getQuaternion(qi, qj, qk, qr) || bno.getGameRotationVector(qi, qj, qk, qr);
    bno.getLinearAccel(lax, lay, laz);
    bno.getGyroscope(gx, gy, gz);

    int16_t p[10];
    p[0] = (int16_t)(qr * 10000.0f);
    p[1] = (int16_t)(qi * 10000.0f);
    p[2] = (int16_t)(qj * 10000.0f);
    p[3] = (int16_t)(qk * 10000.0f);
    p[4] = (int16_t)(lax * 100.0f);
    p[5] = (int16_t)(lay * 100.0f);
    p[6] = (int16_t)(laz * 100.0f);
    p[7] = (int16_t)(gx * 1000.0f);
    p[8] = (int16_t)(gy * 1000.0f);
    p[9] = (int16_t)(gz * 1000.0f);

    imu_data_str = String(p[0]) + "," + String(p[1]) + "," + String(p[2]) + "," + String(p[3]) + "," +
                   String(p[4]) + "," + String(p[5]) + "," + String(p[6]) + "," +
                   String(p[7]) + "," + String(p[8]) + "," + String(p[9]);
  }

  Bridge.update();
  delay(1);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "FAST_IMU_READY"
