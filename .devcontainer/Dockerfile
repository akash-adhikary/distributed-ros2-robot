# ==============================================================================
# Base Image: ROS 2 Jazzy Jalisco on Ubuntu 24.04 LTS (Noble Numbat)
# ==============================================================================
FROM osrf/ros:jazzy-desktop-noble

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools, Gazebo Harmonic, Nav2, and SLAM Toolbox
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    sudo \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-argcomplete \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-slam-toolbox \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-xacro \
    rsync \
    openssh-client \
    udev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure developer user 'ros' (handling default 'ubuntu' user on Ubuntu 24.04)
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=1000

RUN if id "ubuntu" >/dev/null 2>&1; then \
        usermod -l $USERNAME ubuntu 2>/dev/null || true; \
        groupmod -n $USERNAME ubuntu 2>/dev/null || true; \
        usermod -d /home/$USERNAME -m $USERNAME 2>/dev/null || true; \
    elif ! id -u $USER_UID >/dev/null 2>&1; then \
        groupadd --gid $USER_GID $USERNAME && \
        useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME; \
    fi && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# Initialize rosdep for the system
RUN rosdep init 2>/dev/null || true

# Switch to developer user
USER $USERNAME
WORKDIR /home/$USERNAME/my_robot_ws

# Set up automatic ROS 2 environment sourcing & DDS networking
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/$USERNAME/.bashrc && \
    echo "if [ -f /home/$USERNAME/my_robot_ws/install/setup.bash ]; then source /home/$USERNAME/my_robot_ws/install/setup.bash; fi" >> /home/$USERNAME/.bashrc && \
    echo "export ROS_DOMAIN_ID=42" >> /home/$USERNAME/.bashrc && \
    echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> /home/$USERNAME/.bashrc && \
    echo "alias cbuild='colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4'" >> /home/$USERNAME/.bashrc

CMD ["/bin/bash"]
