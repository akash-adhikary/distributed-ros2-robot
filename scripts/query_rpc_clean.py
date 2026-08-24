import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Install msgpack on Uno Q host python and test the RPC bridge
child.sendline("sudo apt-get install -y python3-msgpack")
idx = child.expect([r'password for arduino:', r'\$'], timeout=10)
if idx == 0:
    child.sendline("Askaban78@#")
    child.expect(r'\$', timeout=30)

child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(1)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'req = msgpack.packb([0, 1, \'scanI2C\', []])\n'
's.sendall(req)\n'
'resp = s.recv(1024)\n'
'msg_type, msg_id, error, result = msgpack.unpackb(resp)\n'
'if result != -1:\n'
'    print(f\' SUCCESS: BNO08x detected on STM32 I2C bus at address: {hex(result)} (dec {result})\')\n'
'else:\n'
'    print(\' NO_DEVICE: No I2C device responded on header pins.\')\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
