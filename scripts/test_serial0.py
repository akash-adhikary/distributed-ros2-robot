import pexpect, sys

bash_script = """
set -e
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("HELLO WORLD FROM SERIAL 0!");
}
void loop() {
  Serial.println("ALIVE_TEST_SERIAL0");
  delay(500);
}
SKETCH
echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null

echo "Stopping router..."
echo 'Askaban78@#' | sudo -S systemctl stop arduino-router

echo "Setting up ttyHS1..."
sudo stty -F /dev/ttyHS1 115200 raw -echo -hupcl

echo "Waking MCU..."
sudo /usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1

echo "Reading ttyHS1..."
timeout 5 cat /dev/ttyHS1 || true
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
