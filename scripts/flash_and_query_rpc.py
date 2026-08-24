import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Flash the compiled RPC binary to STM32
child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=60)

# Restart arduino-router to pick up the new bridge session
child.sendline("sudo systemctl restart arduino-router")
idx = child.expect([r'password for arduino:', r'\$'], timeout=10)
if idx == 0:
    child.sendline("Askaban78@#")
    child.expect(r'\$', timeout=15)

# Query the scanI2C RPC method via Python msgpack-rpc
child.sendline('python3 -c "\n'
'import socket, msgpack, time\n'
'time.sleep(2)\n'
's = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n'
's.connect(\'/var/run/arduino-router.sock\')\n'
'# MessagePack-RPC request: [0 (type=REQUEST), 1 (msg_id), \'scanI2C\', []]\n'
'req = msgpack.packb([0, 1, \'scanI2C\', []])\n'
's.sendall(req)\n'
'resp = s.recv(1024)\n'
'unpacked = msgpack.unpackb(resp)\n'
'print(\'=== RPC RESPONSE ===\', unpacked)\n'
's.close()\n'
'"')
child.expect(r'\$', timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
