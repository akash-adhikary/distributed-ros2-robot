import pexpect, sys

bash_script = """
set -e
echo "Killing gpioset..."
echo 'Askaban78@#' | sudo -S killall gpioset || true

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
child.expect([r'ALL_DONE'], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
