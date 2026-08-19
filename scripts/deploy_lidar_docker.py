import pexpect
import sys

ip = "192.168.1.17"
user = "arduino"
password = "Askaban78@#"

commands = [
    # 1. Create workspace and clone RPLIDAR ROS 2 driver
    "mkdir -p /home/arduino/pendrive/ros_ws/src",
    "cd /home/arduino/pendrive/ros_ws/src && if [ ! -d 'rplidar_ros' ]; then git clone -b ros2 https://github.com/Slamtec/rplidar_ros.git; fi",
    
    # 2. Create Dockerfile with CycloneDDS and Colcon
    "cat << 'EOF' > /home/arduino/pendrive/ros_ws/Dockerfile\nFROM ros:humble-ros-base\nRUN apt-get update && apt-get install -y python3-colcon-common-extensions ros-humble-rmw-cyclonedds-cpp && rm -rf /var/lib/apt/lists/*\nENV ROS_DOMAIN_ID=42\nENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\nEOF",
    
    # 3. Build the custom Docker image (uno_ros_base)
    "sudo -S docker build -t uno_ros_base /home/arduino/pendrive/ros_ws",
    
    # 4. Build the ROS 2 workspace inside the container
    "sudo docker run --rm -v /home/arduino/pendrive/ros_ws:/ws uno_ros_base bash -c 'source /opt/ros/humble/setup.bash && cd /ws && colcon build'",
    
    # 5. Create a handy startup script for the user on the Uno Q
    "cat << 'EOF' > /home/arduino/start_rplidar.sh\n#!/bin/bash\necho \"Setting permissions...\"\nsudo chmod a+rw /dev/ttyUSB0\necho \"Spinning up motor...\"\npython3 /home/arduino/spin_test.py\necho \"Killing any old docker containers...\"\nsudo docker rm -f rplidar >/dev/null 2>&1\necho \"Starting RPLIDAR ROS 2 Node in Docker...\"\nsudo docker run -d --name rplidar --net=host --privileged \\\n  -v /home/arduino/pendrive/ros_ws:/ws \\\n  -v /dev/ttyUSB0:/dev/ttyUSB0 \\\n  uno_ros_base \\\n  bash -c \"source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && ros2 launch rplidar_ros rplidar_c1_launch.py\"\necho \"Started in background!\"\nEOF",
    
    "chmod +x /home/arduino/start_rplidar.sh"
]

ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip}"
print(f"Connecting to {ssh_cmd}...")

child = pexpect.spawn(ssh_cmd, encoding='utf-8')
child.logfile = sys.stdout

try:
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if idx == 0:
        child.sendline(password)
        child.expect(r'\$', timeout=10)
        
        for cmd in commands:
            print(f"\n---> Executing: {cmd.split(' ')[0]} ...")
            child.sendline(cmd)
            
            if "sudo -S" in cmd:
                idx2 = child.expect(['password for arduino:', r'\$'], timeout=10)
                if idx2 == 0:
                    child.sendline(password)
                    # Building docker / compiling colcon takes time
                    child.expect(r'\$', timeout=600)
            elif "colcon build" in cmd:
                child.expect(r'\$', timeout=600)
            else:
                child.expect(r'\$', timeout=60)
                
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n✅ Deployment completed successfully!")
    else:
        print("\n❌ Failed to connect.")
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
