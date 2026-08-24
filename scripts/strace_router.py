import pexpect, sys

bash_script = """
set -e
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
void setup() {
  Serial1.begin(115200);
  delay(1000);
  Serial1.println("HELLO UART FROM UNO Q!");
}
void loop() {
  Serial1.println("ALIVE_TEST");
  delay(1000);
}
SKETCH
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "Tracing router..."
echo 'Askaban78@#' | sudo -S strace -p $(pidof arduino-router) -s 9999 -e read -c -w &
STRACE_PID=$!
sleep 5
sudo kill -INT $STRACE_PID
echo "Trace done!"
echo 'Askaban78@#' | sudo -S strace -p $(pidof arduino-router) -s 9999 -e read 2>&1 | head -n 30
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
