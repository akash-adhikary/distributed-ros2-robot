#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int found_w0 = -1;
int found_w2 = -1;
int scan_count = 0;

int get_w0() { return found_w0; }
int get_w2() { return found_w2; }
int get_sc() { return scan_count; }

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/w0", get_w0);
  Bridge.provide("i2c/w2", get_w2);
  Bridge.provide("i2c/sc", get_sc);

  // Set pin D4 HIGH (RST)
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);

  Wire.begin();
#if defined(Wire2)
  Wire2.begin();
#endif
}

void loop() {
  found_w0 = -1;
  found_w2 = -1;

  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) { found_w0 = a; break; }
  }

#if defined(Wire2)
  for (uint8_t a = 1; a < 127; a++) {
    Wire2.beginTransmission(a);
    if (Wire2.endTransmission() == 0) { found_w2 = a; break; }
  }
#endif

  scan_count++;
  Bridge.update();
  delay(100);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << 'PYEOF' > ~/live_i2c_check.py
import socket, msgpack, time, sys

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

try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/var/run/arduino-router.sock')
    print('Scanning all I2C ports continuously (Press Ctrl+C to exit)...')
    print('='*60)
    while True:
        sc = call_mcu(s, 'i2c/sc') or 0
        w0 = call_mcu(s, 'i2c/w0')
        w2 = call_mcu(s, 'i2c/w2')
        w0_str = hex(w0) if w0 and w0 > 0 else 'None'
        w2_str = hex(w2) if w2 and w2 > 0 else 'None'
        print(f'Scan #{sc:04d} | Dedicated SDA/SCL: {w0_str:<6} | A4/A5 Header: {w2_str:<6}', end='\r')
        sys.stdout.flush()
        time.sleep(0.2)
except KeyboardInterrupt:
    print('\nExiting scanner.')
finally:
    try: s.close()
    except: pass
PYEOF
