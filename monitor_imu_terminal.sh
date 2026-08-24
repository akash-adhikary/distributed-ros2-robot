#!/bin/bash
set -e

echo "Connecting to Uno Q live sensor monitor..."
echo "=========================================================================="
echo "Live BNO08x Sensor Terminal Feed (Press Ctrl+C to exit)"
echo "=========================================================================="

ssh -o StrictHostKeyChecking=no arduino@192.168.1.17 "python3 -u ~/monitor_bno.py"
