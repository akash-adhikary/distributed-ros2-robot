import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cp /home/arduino/Arduino/libraries/Arduino_RouterBridge/examples/monitor/monitor.ino ~/BnoTest/BnoTest.ino
echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
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
echo "Running python..."
python3 ~/read_sock.py
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
child.expect([r'ALL_DONE'], timeout=200)

child.sendline("exit")
child.expect(pexpect.EOF)
