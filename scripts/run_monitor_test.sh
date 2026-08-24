#!/bin/bash
set -e
cp /home/arduino/Arduino/libraries/Arduino_RouterBridge/examples/monitor/monitor.ino ~/BnoTest/
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
cat << "PY" > ~/read_sock.py
import socket, msgpack, time
time.sleep(2)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/var/run/arduino-router.sock')
    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)
    print('=== READING DEBUG VIA BRIDGE ===')
    start = time.time()
    count = 0
    while time.time() - start < 10 and count < 10:
        s.settimeout(1)
        try:
            buf = s.recv(1024)
            if not buf: break
            unpacker.feed(buf)
            for msg in unpacker:
                print('RECV:', msg)
                count += 1
        except socket.timeout:
            pass
except Exception as e:
    print('Err:', e)
finally:
    s.close()
PY
python3 ~/read_sock.py
