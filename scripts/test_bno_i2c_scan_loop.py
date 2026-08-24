import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int found_addr = -1;

int get_found() {
  return found_addr;
}

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/scan", get_found);
  Wire.begin();
}

void loop() {
  int f = 0;
  for (byte address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    byte error = Wire.endTransmission();
    if (error == 0) {
      f = (int)address;
      break;
    }
  }
  found_addr = f;
  Bridge.update();
  delay(100);
}
SKETCH

echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
cat << "PY" > ~/query_scan.py
import socket, msgpack, time
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/var/run/arduino-router.sock')
    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)
    req = msgpack.packb([0, 1, "i2c/scan", []])
    s.sendall(req)
    time.sleep(0.5)
    buf = s.recv(1024)
    unpacker.feed(buf)
    for msg in unpacker:
        print("SCAN_RESULT:", msg)
except Exception as e:
    print("Err:", e)
finally:
    s.close()
PY
python3 ~/query_scan.py
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
