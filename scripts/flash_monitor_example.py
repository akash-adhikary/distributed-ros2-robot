import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cp /home/arduino/Arduino/libraries/Arduino_RouterBridge/examples/monitor/monitor.ino ~/BnoTest/")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && echo COMPILE_DONE")
child.expect([r'COMPILE_DONE'], timeout=180)
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest && echo UPLOAD_DONE")
child.expect([r'UPLOAD_DONE'], timeout=120)
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router && echo ROUTER_RESTARTED")
child.expect([r'ROUTER_RESTARTED'], timeout=15)
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Read bridge socket for notify
child.sendline('cat << "PY" > ~/read_sock.py\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
'try:\n'
'    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
'    s.connect(\'/var/run/arduino-router.sock\')\n'
'    unpacker = msgpack.Unpacker(max_buffer_size=10240, max_array_len=100)\n'
'    print(\'=== READING DEBUG VIA BRIDGE ===\')\n'
'    start = time.time()\n'
'    count = 0\n'
'    while time.time() - start < 10 and count < 10:\n'
'        s.settimeout(1)\n'
'        try:\n'
'            buf = s.recv(1024)\n'
'            if not buf: break\n'
'            unpacker.feed(buf)\n'
'            for msg in unpacker:\n'
'                print(\'RECV:\', msg)\n'
'                count += 1\n'
'        except socket.timeout:\n'
'            pass\n'
'except Exception as e:\n'
'    print(\'Err:\', e)\n'
'finally:\n'
'    s.close()\n'
'PY\n')
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 ~/read_sock.py && echo READ_DONE")
child.expect([r'READ_DONE'], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
