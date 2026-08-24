#!/bin/bash
set -e

cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

int d2_val = -1;
int get_d2() { return d2_val; }

void setup() {
  Bridge.begin();
  Bridge.provide("pin/d2", get_d2);
  pinMode(2, INPUT_PULLUP);
}

void loop() {
  d2_val = digitalRead(2);
  Bridge.update();
  delay(10);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << 'PYEOF' > ~/check_d2.py
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

for i in range(5):
    val = call_mcu('pin/d2')
    print(f'Pin D2 Logic Level: {val} ({"HIGH / Idle" if val == 1 else "LOW / Asserted" if val == 0 else "None"})')
    time.sleep(0.2)
s.close()
PYEOF
python3 ~/check_d2.py
