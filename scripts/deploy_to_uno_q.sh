#!/usr/bin/env bash
# ==============================================================================
# Deployment Script for Arduino UNO Q (Qualcomm QRB2210 Debian Linux SBC)
# ==============================================================================
set -e

# Default Connection Settings (Can be overridden via environment variables or args)
ROBOT_HOST="${1:-uno-q.local}"
ROBOT_USER="${2:-debian}"
REMOTE_DEST="${3:-/home/${ROBOT_USER}/robot_deploy}"
DRY_RUN="${4:-false}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "${SCRIPT_DIR}")"

echo "============================================================"
echo " Deploying Robot Code to Arduino UNO Q Edge SBC"
echo " Target Host : ${ROBOT_USER}@${ROBOT_HOST}"
echo " Destination : ${REMOTE_DEST}"
echo " Source Path : ${WORKSPACE_ROOT}/uno_q_firmware"
echo "============================================================"

# Check if rsync and ssh are available
command -v rsync >/dev/null 2>&1 || { echo "ERROR: rsync is required on host PC."; exit 1; }
command -v ssh >/dev/null 2>&1 || { echo "ERROR: ssh is required on host PC."; exit 1; }

RSYNC_OPTS="-avz --delete --exclude='*.git*' --exclude='__pycache__' --exclude='*.pyc'"

if [ "${DRY_RUN}" = "--dry-run" ] || [ "${DRY_RUN}" = "true" ]; then
    echo "==> Performing dry run (no files transferred)..."
    RSYNC_OPTS="${RSYNC_OPTS} --dry-run"
fi

# Ensure remote target directory exists
if [ "${DRY_RUN}" != "--dry-run" ] && [ "${DRY_RUN}" != "true" ]; then
    echo "==> Ensuring remote directory exists..."
    ssh -o ConnectTimeout=5 "${ROBOT_USER}@${ROBOT_HOST}" "mkdir -p ${REMOTE_DEST}"
fi

# Synchronize firmware and bridge files
echo "==> Syncing uno_q_firmware to remote edge board..."
rsync ${RSYNC_OPTS} \
    "${WORKSPACE_ROOT}/uno_q_firmware/" \
    "${ROBOT_USER}@${ROBOT_HOST}:${REMOTE_DEST}/uno_q_firmware/"

echo "============================================================"
echo " Deployment to ${ROBOT_HOST} completed successfully!"
echo "============================================================"
