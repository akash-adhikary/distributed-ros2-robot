#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#define BNO_USE_I2C
#include <7Semi_BNO08x.h>

static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, 2, -1);
static BNO08x_7Semi bno(bus);

int f_len = 0;
int f_b0 = 0, f_b1 = 0, f_b2 = 0, f_b3 = 0, f_b4 = 0, f_b5 = 0, f_b6 = 0, f_b7 = 0;
int f_b8 = 0, f_b9 = 0, f_b10 = 0, f_b11 = 0, f_b12 = 0, f_b13 = 0;
int total_frames = 0;

int get_len() { return f_len; }
int get_tot() { return total_frames; }
int get_b0() { return f_b0; }
int get_b1() { return f_b1; }
int get_b2() { return f_b2; }
int get_b3() { return f_b3; }
int get_b4() { return f_b4; }
int get_b5() { return f_b5; }
int get_b6() { return f_b6; }
int get_b7() { return f_b7; }
int get_b8() { return f_b8; }
int get_b9() { return f_b9; }
int get_b10() { return f_b10; }
int get_b11() { return f_b11; }
int get_b12() { return f_b12; }
int get_b13() { return f_b13; }

void setup() {
  Bridge.begin();
  Bridge.provide("f/len", get_len);
  Bridge.provide("f/tot", get_tot);
  Bridge.provide("f/b0", get_b0);
  Bridge.provide("f/b1", get_b1);
  Bridge.provide("f/b2", get_b2);
  Bridge.provide("f/b3", get_b3);
  Bridge.provide("f/b4", get_b4);
  Bridge.provide("f/b5", get_b5);
  Bridge.provide("f/b6", get_b6);
  Bridge.provide("f/b7", get_b7);
  Bridge.provide("f/b8", get_b8);
  Bridge.provide("f/b9", get_b9);
  Bridge.provide("f/b10", get_b10);
  Bridge.provide("f/b11", get_b11);
  Bridge.provide("f/b12", get_b12);
  Bridge.provide("f/b13", get_b13);

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
  if (n >= 4) {
    total_frames++;
    if (n > 4 || total_frames % 20 == 0) {
      f_len = n;
      f_b0 = buf[0];
      f_b1 = buf[1];
      f_b2 = buf[2];
      f_b3 = buf[3];
      f_b4 = (n > 4) ? buf[4] : 0;
      f_b5 = (n > 5) ? buf[5] : 0;
      f_b6 = (n > 6) ? buf[6] : 0;
      f_b7 = (n > 7) ? buf[7] : 0;
      f_b8 = (n > 8) ? buf[8] : 0;
      f_b9 = (n > 9) ? buf[9] : 0;
      f_b10 = (n > 10) ? buf[10] : 0;
      f_b11 = (n > 11) ? buf[11] : 0;
      f_b12 = (n > 12) ? buf[12] : 0;
      f_b13 = (n > 13) ? buf[13] : 0;
    }
  }

  Bridge.update();
  delay(5);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "PRINT_BYTES_READY"
