#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int found_bus0_addr = -1;
int found_bus1_addr = -1;

int get_b0() { return found_bus0_addr; }
int get_b1() { return found_bus1_addr; }

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/b0", get_b0);
  Bridge.provide("i2c/b1", get_b1);

  // Bring BNO08x out of reset (Pin D4 HIGH)
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);
  delay(10);
  digitalWrite(4, LOW);
  delay(10);
  digitalWrite(4, HIGH);
  delay(300);

  // Scan Wire (Standard)
  Wire.begin();
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      found_bus0_addr = addr;
      break;
    }
  }

  // Scan Wire1 if available
#if defined(Wire1) || defined(WIRE_INTERFACES_COUNT) && WIRE_INTERFACES_COUNT > 1
  Wire1.begin();
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire1.beginTransmission(addr);
    if (Wire1.endTransmission() == 0) {
      found_bus1_addr = addr;
      break;
    }
  }
#endif
}

void loop() {
  Bridge.update();
  delay(50);
}
SKETCH

echo "Compiling Dual Bus Scanner with RST pulse..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << 'PYEOF' > ~/check_both_buses.py
import socket, msgpack, time

def call_mcu(s, m):
    try:
        s.sendall(msgpack.packb([0, 1, m, []]))
        time.sleep(0.01)
        buf = s.recv(1024)
        u = msgpack.Unpacker()
        u.feed(buf)
        for msg in u: return msg[3]
    except: pass
    return None

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
b0 = call_mcu(s, 'i2c/b0')
b1 = call_mcu(s, 'i2c/b1')
print('====================================')
print('Wire (Bus 0) Found:', hex(b0) if b0 and b0 > 0 else 'None')
print('Wire1 (Bus 1) Found:', hex(b1) if b1 and b1 > 0 else 'None')
print('====================================')
s.close()
PYEOF
python3 ~/check_both_buses.py
