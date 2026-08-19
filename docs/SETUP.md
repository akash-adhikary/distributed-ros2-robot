# Setup Guide: Reproducible Environment & Build Instructions

This document records the exact steps to reproduce, build, and verify the `my_robot_ws` workspace using either **Docker Dev Containers** (recommended) or **Native Ubuntu**.

---

## Option 1: VS Code Dev Containers / Docker (Fully Reproducible)

### Prerequisites:
- Docker Engine & Docker Compose installed.
- VS Code with the **Dev Containers** (`ms-vscode-remote.remote-containers`) extension.

### Quickstart:
1. Open this workspace directory in VS Code:
   ```bash
   code /path/to/my_robot_ws
   ```
2. When prompted with **"Reopen in Container"**, click it.
   *(Or press `F1` / `Ctrl+Shift+P`, type `Dev Containers: Reopen in Container`, and press Enter).*
3. The DevContainer will build the pinned **ROS 2 Jazzy + Gazebo Harmonic + Nav2** image, configure GUI pass-through for simulation, and run `scripts/install_deps.sh`.
4. Open the integrated terminal and compile the workspace:
   ```bash
   cbuild
   ```

### Plain Docker Build (CLI Alternative):
If you want to build and run the container purely from the terminal without VS Code:
```bash
# Build the Docker image
docker build -t my_robot_ws:jazzy -f .devcontainer/Dockerfile .

# Run container with X11 GUI forwarding
xhost +local:root
docker run -it --rm \
    --net=host \
    --ipc=host \
    --privileged \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(pwd):/home/ros/my_robot_ws \
    my_robot_ws:jazzy bash
```

---

## Option 2: Native Ubuntu Setup

If developing directly on the host machine:

### 1. Add ROS 2 Repositories
```bash
sudo apt update && sudo apt install -y locales curl gnupg2 lsb-release software-properties-common
sudo add-apt-repository -y universe

sudo install -m 0755 -d /etc/apt/keyrings
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo tee /etc/apt/keyrings/ros-archive-keyring.gpg > /dev/null
sudo chmod 644 /etc/apt/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### 2. Install Core Stacks & Build Tools
```bash
sudo apt update
sudo apt install -y \
    ros-${ROS_DISTRO}-desktop \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool
```

### 3. Install Workspace Dependencies
Run the idempotent dependency installer:
```bash
bash scripts/install_deps.sh
```

---

## Building and Sourcing the Workspace

Inside the workspace root (`my_robot_ws`):

```bash
# Build all packages with symlink-install (saves disk space on 90GB SSD)
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4

# Source the local overlay
source install/setup.bash
```

---

## Deploying to Uno Q Edge Hardware

When deploying the robot firmware and bridge scripts to the Uno Q board:
```bash
# Test deployment dry run
bash scripts/deploy_to_uno_q.sh uno-q.local debian /home/debian/robot_deploy --dry-run

# Live deployment
bash scripts/deploy_to_uno_q.sh uno-q.local debian /home/debian/robot_deploy
```
