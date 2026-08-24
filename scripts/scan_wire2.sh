#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int found_w0 = -1;
int found_w1 = -1;
int found_w2 = -1;

int get_w0() { return found_w0; }
int get_w1() { return found_w1; }
int get_w2() { return found_w2; }

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/w0", get_w0);
  Bridge.provide("i2c/w1", get_w1);
  Bridge.provide("i2c/w2", get_w2);

  // Pin D4 HIGH (RST)
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);
  delay(10);
  digitalWrite(4, LOW);
  delay(10);
  digitalWrite(4, HIGH);
  delay(300);

  // Scan Wire (Top dedicated SDA/SCL pins)
  Wire.begin();
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) { found_w0 = a; break; }
  }

#if defined(Wire1)
  Wire1.begin();
  for (uint8_t a = 1; a < 127; a++) {
    Wire1.beginTransmission(a);
    if (Wire1.endTransmission() == 0) { found_w1 = a; break; }
  }
#endif

#if defined(Wire2)
  Wire2.begin();
  for (uint8_t a = 1; a < 127; a++) {
    Wire2.beginTransmission(a);
    if (Wire2.endTransmission() == 0) { found_w2 = a; break; }
  }
#endif
}

void loop() {
  Bridge.update();
  delay(50);
}
SKETCH

echo "Compiling Wire2 (A4/A5) Scanner..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << 'PYEOF' > ~/check_wire2.py
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
w0 = call_mcu(s, 'i2c/w0')
w1 = call_mcu(s, 'i2c/w1')
w2 = call_mcu(s, 'i2c/w2')
print('==============================================')
print('Wire (Top dedicated pins) Found:', hex(w0) if w0 and w0 > 0 else 'None')
print('Wire1 Found:', hex(w1) if w1 and w1 > 0 else 'None')
print('Wire2 (Analog pins A4/A5) Found:', hex(w2) if w2 and w2 > 0 else 'None')
print('==============================================')
s.close()
PYEOF
python3 ~/check_wire2.py
