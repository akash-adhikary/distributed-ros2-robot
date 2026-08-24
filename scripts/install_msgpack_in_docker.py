import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker run --rm ros:jazzy-ros-base apt-get update && docker run --name temp_msgpack ros:jazzy-ros-base bash -c 'apt-get update && apt-get install -y python3-msgpack' && docker commit temp_msgpack ros:jazzy-ros-base && docker rm temp_msgpack")
child.expect([r'\$ '], timeout=180)

child.sendline("docker restart bno08x_ros")
child.expect([r'\$ '], timeout=15)

child.sendline("sleep 2 && docker logs --tail 10 bno08x_ros")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
