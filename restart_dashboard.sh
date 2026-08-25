#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Restarting Dashboard Control Hub..."
"$SCRIPT_DIR/stop_dashboard.sh"
sleep 1.5
"$SCRIPT_DIR/start_dashboard.sh"
