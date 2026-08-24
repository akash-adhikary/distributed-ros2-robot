#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int last_rx_len = 0;
int rx_count = 0;
int roll_deg = 0, pitch_deg = 0, yaw_deg = 0;
int q_r = 10000, q_i = 0, q_j = 0, q_k = 0;

int get_len() { return last_rx_len; }
int get_cnt() { return rx_count; }
int get_r() { return roll_deg; }
int get_p() { return pitch_deg; }
int get_y() { return yaw_deg; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }

void send_enable_report(uint8_t addr, TwoWire& wire, uint8_t report_id, uint32_t interval_us) {
  uint8_t cmd[21] = {0};
  cmd[0] = 21; // length LSB
  cmd[1] = 0;  // length MSB
  cmd[2] = 2;  // channel 2 (Control)
  cmd[3] = 0;  // seq

  cmd[4] = 0xFD; // SET_FEATURE
  cmd[5] = report_id;
  cmd[6] = 0;    // flags
  cmd[7] = 0;    // change sensitivity LSB
  cmd[8] = 0;    // change sensitivity MSB
  cmd[9] = (uint8_t)(interval_us & 0xFF);
  cmd[10] = (uint8_t)((interval_us >> 8) & 0xFF);
  cmd[11] = (uint8_t)((interval_us >> 16) & 0xFF);
  cmd[12] = (uint8_t)((interval_us >> 24) & 0xFF);

  wire.beginTransmission(addr);
  wire.write(cmd, 21);
  wire.endTransmission();
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/len", get_len);
  Bridge.provide("imu/cnt", get_cnt);
  Bridge.provide("imu/roll", get_r);
  Bridge.provide("imu/pitch", get_p);
  Bridge.provide("imu/yaw", get_y);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);

  Wire.begin();
  Wire2.begin();
  delay(200);

  // Send Enable Rotation Vector (0x05) at 20ms (20000us)
  send_enable_report(0x4B, Wire, 0x05, 20000);
  send_enable_report(0x4B, Wire2, 0x05, 20000);
  send_enable_report(0x4A, Wire, 0x05, 20000);
  send_enable_report(0x4A, Wire2, 0x05, 20000);
}

void process_wire(uint8_t addr, TwoWire& wire) {
  // 1. Read SHTP 4-byte header
  uint8_t hdr_cnt = wire.requestFrom(addr, (uint8_t)4);
  if (hdr_cnt < 4) return;

  uint8_t b0 = wire.read();
  uint8_t b1 = wire.read();
  uint8_t channel = wire.read();
  uint8_t seq = wire.read();

  uint16_t packet_len = (b0 | (b1 << 8)) & 0x7FFF;
  if (packet_len < 4 || packet_len > 128) return;

  last_rx_len = packet_len;

  // 2. Read remainder of payload
  uint8_t payload[128];
  payload[0] = b0; payload[1] = b1; payload[2] = channel; payload[3] = seq;

  uint16_t rem = packet_len - 4;
  if (rem > 0) {
    uint8_t got = wire.requestFrom(addr, (uint8_t)rem);
    for (uint16_t i = 0; i < got && (i + 4) < 128; i++) {
      payload[4 + i] = wire.read();
    }
  }

  // Parse Rotation Vector if report ID 0x05 or 0x08
  if (packet_len >= 19 && (payload[9] == 0x05 || payload[9] == 0x08)) {
    int16_t raw_i = (int16_t)(payload[13] | (payload[14] << 8));
    int16_t raw_j = (int16_t)(payload[15] | (payload[16] << 8));
    int16_t raw_k = (int16_t)(payload[17] | (payload[18] << 8));
    int16_t raw_r = (int16_t)(payload[19] | (payload[20] << 8));

    float qi = raw_i / 16384.0f;
    float qj = raw_j / 16384.0f;
    float qk = raw_k / 16384.0f;
    float qr = raw_r / 16384.0f;

    q_r = (int)(qr * 10000.0f);
    q_i = (int)(qi * 10000.0f);

    float sinr_cosp = 2.0f * (qr * qi + qj * qk);
    float cosr_cosp = 1.0f - 2.0f * (qi * qi + qj * qj);
    roll_deg = (int)(atan2(sinr_cosp, cosr_cosp) * 180.0f / 3.14159265f);

    float sinp = 2.0f * (qr * qj - qk * qi);
    if (fabs(sinp) >= 1.0f) pitch_deg = (int)copysign(90.0f, sinp);
    else pitch_deg = (int)(asin(sinp) * 180.0f / 3.14159265f);

    float siny_cosp = 2.0f * (qr * qk + qi * qj);
    float cosy_cosp = 1.0f - 2.0f * (qj * qj + qk * qk);
    yaw_deg = (int)(atan2(siny_cosp, cosy_cosp) * 180.0f / 3.14159265f);

    rx_count++;
  }
}

void loop() {
  process_wire(0x4B, Wire);
  process_wire(0x4B, Wire2);
  process_wire(0x4A, Wire);
  process_wire(0x4A, Wire2);

  Bridge.update();
  delay(10);
}
SKETCH

echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "SHTP_RX_READY"
