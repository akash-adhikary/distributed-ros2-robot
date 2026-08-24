#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>

Adafruit_BNO08x bno(-1);
sh2_SensorValue_t sensorValue;

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

  Wire2.begin();
  delay(100);

  if (bno.begin_I2C(0x4B, &Wire2)) {
    sensor_active = 1;
    bno.enableReport(SH2_GAME_ROTATION_VECTOR, 20000);
    bno.enableReport(SH2_ROTATION_VECTOR, 20000);
  }
}

void loop() {
  if (sensor_active == 1) {
    if (bno.wasReset()) {
      bno.enableReport(SH2_GAME_ROTATION_VECTOR, 20000);
      bno.enableReport(SH2_ROTATION_VECTOR, 20000);
    }

    if (bno.getSensorEvent(&sensorValue)) {
      if (sensorValue.sensorId == SH2_GAME_ROTATION_VECTOR || sensorValue.sensorId == SH2_ROTATION_VECTOR) {
        float qr = sensorValue.un.gameRotationVector.real;
        float qi = sensorValue.un.gameRotationVector.i;
        float qj = sensorValue.un.gameRotationVector.j;
        float qk = sensorValue.un.gameRotationVector.k;

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
    }
  } else {
    if (bno.begin_I2C(0x4B, &Wire2)) {
      sensor_active = 1;
      bno.enableReport(SH2_GAME_ROTATION_VECTOR, 20000);
      bno.enableReport(SH2_ROTATION_VECTOR, 20000);
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
echo "ADAFRUIT_WIRE2_READY"
