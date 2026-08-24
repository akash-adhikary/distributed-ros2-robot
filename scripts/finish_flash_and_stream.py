import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Upload the compiled BNO08x reader binary to STM32
child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=60)

# Restart router bridge
child.sendline("sudo systemctl restart arduino-router")
idx = child.expect([r'password for arduino:', r'\$'], timeout=10)
if idx == 0:
    child.sendline("Askaban78@#")
    child.expect(r'\$', timeout=10)

# Query live quaternions and angular velocity
child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'for i in range(5):\n'
'    req = msgpack.packb([0, i+1, \'getIMUData\', []])\n'
'    s.sendall(req)\n'
'    resp = bytearray()\n'
'    while True:\n'
'        chunk = s.recv(1024)\n'
'        if not chunk: break\n'
'        resp.extend(chunk)\n'
'        try:\n'
'            data = msgpack.unpackb(resp, max_array_len=100)\n'
'            msg_type, msg_id, err, result = data\n'
'            qx, qy, qz, qw, gx, gy, gz = result\n'
'            print(f\'Sample {i+1} -> Quat: (x={qx:.4f}, y={qy:.4f}, z={qz:.4f}, w={qw:.4f}) | Gyro: (gx={gx:.3f}, gy={gy:.3f}, gz={gz:.3f})\')\n'
'            break\n'
'        except Exception:\n'
'            pass\n'
'    time.sleep(0.1)\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
