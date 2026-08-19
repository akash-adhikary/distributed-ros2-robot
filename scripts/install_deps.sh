#!/usr/bin/env bash
# ==============================================================================
# Idempotent Dependency Installation Script (rosdep + apt only)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "${SCRIPT_DIR}")"

echo "==> [my_robot_ws] Checking system dependencies..."

# Ensure we are in a valid environment
if ! command -v apt-get >/dev/null 2>&1; then
    echo "ERROR: apt-get package manager not found. This script requires a Debian/Ubuntu system."
    exit 1
fi

# 1. Update apt repositories idempotently
echo "==> Updating package indices..."
sudo apt-get update

# 2. Ensure rosdep and core build utilities are installed via apt
sudo apt-get install -y --no-install-recommends \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool

# 3. Initialize rosdep if not already initialized
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    echo "==> Initializing rosdep sources..."
    sudo rosdep init 2>/dev/null || true
fi

echo "==> Updating rosdep index..."
rosdep update

# 4. Resolve and install all workspace package dependencies from package.xml files
echo "==> Resolving workspace dependencies via rosdep..."
rosdep install \
    --from-paths "${WORKSPACE_ROOT}/src" \
    --ignore-src \
    --rosdistro "${ROS_DISTRO:-jazzy}" \
    -y \
    -r

echo "==> [my_robot_ws] All dependencies successfully installed and verified!"
