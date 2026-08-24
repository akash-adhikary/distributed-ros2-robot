#!/bin/bash
set -e

echo "Connecting to live Uno Q I2C bus scanner..."
echo "=========================================================================="
echo "Live Hardware I2C Detection (Press Ctrl+C to exit)"
echo "=========================================================================="

ssh -o StrictHostKeyChecking=no arduino@192.168.1.17 "python3 -u ~/live_i2c_check.py"
