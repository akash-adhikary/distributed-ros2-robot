#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int found_address = -1;
int error_code = -1;

int get_found() { return found_address; }
int get_err() { return error_code; }

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/found", get_found);
  Bridge.provide("i2c/err", get_err);

  Wire.begin();
  delay(200);

  // Scan all 127 I2C addresses
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
      found_address = addr;
      break;
    }
  }
}

void loop() {
  Bridge.update();
  delay(50);
}
SKETCH

echo "Compiling I2C scanner..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
echo "Uploading I2C scanner..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "SCANNER_READY"
