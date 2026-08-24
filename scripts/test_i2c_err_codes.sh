#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int err_w0_4b = -1;
int err_w0_4a = -1;
int err_w2_4b = -1;
int err_w2_4a = -1;

int get_e0_4b() { return err_w0_4b; }
int get_e0_4a() { return err_w0_4a; }
int get_e2_4b() { return err_w2_4b; }
int get_e2_4a() { return err_w2_4a; }

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/e0_4b", get_e0_4b);
  Bridge.provide("i2c/e0_4a", get_e0_4a);
  Bridge.provide("i2c/e2_4b", get_e2_4b);
  Bridge.provide("i2c/e2_4a", get_e2_4a);

  Wire.begin();
  Wire2.begin();
}

void loop() {
  Wire.beginTransmission(0x4B);
  err_w0_4b = Wire.endTransmission();

  Wire.beginTransmission(0x4A);
  err_w0_4a = Wire.endTransmission();

  Wire2.beginTransmission(0x4B);
  err_w2_4b = Wire2.endTransmission();

  Wire2.beginTransmission(0x4A);
  err_w2_4a = Wire2.endTransmission();

  Bridge.update();
  delay(100);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << 'PYEOF' > ~/check_i2c_errors.py
import socket, msgpack, time

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')

def call_mcu(m):
    try:
        s.sendall(msgpack.packb([0, 1, m, []]))
        time.sleep(0.01)
        buf = s.recv(1024)
        u = msgpack.Unpacker()
        u.feed(buf)
        for msg in u: return msg[3]
    except: pass
    return None

err_names = {0: "0 (SUCCESS / ACK)", 2: "2 (NACK on Address - No Device Responding)", 3: "3 (NACK on Data)", 4: "4 (Other Error / Bus Stuck)", 5: "5 (Timeout)"}

e0_4b = call_mcu('i2c/e0_4b')
e0_4a = call_mcu('i2c/e0_4a')
e2_4b = call_mcu('i2c/e2_4b')
e2_4a = call_mcu('i2c/e2_4a')

print('=== I2C BUS TRANSMISSION STATUS ===')
print(f'Top Dedicated SDA/SCL (Wire)  @ 0x4B: {err_names.get(e0_4b, str(e0_4b))}')
print(f'Top Dedicated SDA/SCL (Wire)  @ 0x4A: {err_names.get(e0_4a, str(e0_4a))}')
print(f'Analog Pins A4/A5     (Wire2) @ 0x4B: {err_names.get(e2_4b, str(e2_4b))}')
print(f'Analog Pins A4/A5     (Wire2) @ 0x4A: {err_names.get(e2_4a, str(e2_4a))}')
s.close()
PYEOF
python3 ~/check_i2c_errors.py
