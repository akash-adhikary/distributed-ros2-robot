#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, -1, -1);
static BNO08x_7Semi bno(bus);

int b_len = 0;
int b_chan = 0;
int b_rep = 0;
int b_d0 = 0, b_d1 = 0, b_d2 = 0, b_d3 = 0, b_d4 = 0, b_d5 = 0;
int rx_total = 0;

int get_len() { return b_len; }
int get_chan() { return b_chan; }
int get_rep() { return b_rep; }
int get_d0() { return b_d0; }
int get_d1() { return b_d1; }
int get_d2() { return b_d2; }
int get_d3() { return b_d3; }
int get_d4() { return b_d4; }
int get_d5() { return b_d5; }
int get_tot() { return rx_total; }

void setup() {
  Bridge.begin();
  Bridge.provide("raw/len", get_len);
  Bridge.provide("raw/chan", get_chan);
  Bridge.provide("raw/rep", get_rep);
  Bridge.provide("raw/d0", get_d0);
  Bridge.provide("raw/d1", get_d1);
  Bridge.provide("raw/d2", get_d2);
  Bridge.provide("raw/d3", get_d3);
  Bridge.provide("raw/d4", get_d4);
  Bridge.provide("raw/d5", get_d5);
  Bridge.provide("raw/tot", get_tot);

  Wire2.begin();
  delay(100);
  bno.begin();
  delay(100);
  bno.enableRotationVector(20);
  bno.enableAcc(20);
  bno.enableGyro(20);
}

void loop() {
  uint8_t buf[64];
  int n = bno.readPacket(buf, sizeof(buf));
  if (n >= 4) {
    rx_total++;
    b_len = n;
    b_chan = buf[2];
    if (n >= 10) b_rep = buf[9];
    if (n >= 14) b_d0 = buf[13];
    if (n >= 15) b_d1 = buf[14];
    if (n >= 16) b_d2 = buf[15];
    if (n >= 17) b_d3 = buf[16];
    if (n >= 18) b_d4 = buf[17];
    if (n >= 19) b_d5 = buf[18];
  }
  Bridge.update();
  delay(5);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "INSPECT_RAW_READY"
