import pexpect, sys

bash_script = """
set -e
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

int get_test() {
    return 4242;
}

void setup() {
  Bridge.begin();
  Bridge.provide("get_test", get_test);
}
void loop() {
  Bridge.update();
  delay(10);
}
SKETCH
echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Restarting router..."
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << "PY" > ~/query_test.py
import socket, msgpack, time
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/var/run/arduino-router.sock')
    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)
    
    req = msgpack.packb([0, 1, "get_test", []])
    s.sendall(req)
    print("=== SENT REQ ===")
    
    start = time.time()
    while time.time() - start < 3:
        s.settimeout(1)
        try:
            buf = s.recv(1024)
            if not buf: break
            unpacker.feed(buf)
            for msg in unpacker:
                print('RECV:', msg)
        except socket.timeout:
            pass
except Exception as e:
    print('Err:', e)
finally:
    s.close()
PY
echo "Running python read..."
python3 ~/query_test.py
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
