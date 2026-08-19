# MCU Firmware (STM32U585 Real-Time Controller)

This directory contains the firmware running on the **STM32U585 MCU** embedded in the Arduino UNO Q board.

## Responsibilities:
1. **Low-Level Motor Control**: Direct PWM & GPIO control of motor H-Bridge/driver boards.
2. **Quadrature Encoder Decoding**: High-frequency hardware timer/interrupt-based tick counting.
3. **PID Loop**: 50–100 Hz closed-loop speed regulation for left and right wheels.
4. **Safety Watchdog**: Stops motors if velocity commands stop arriving from the MPU within 500ms.
5. **Bridge Communication**: Exchanges commands and encoder odometry with the Debian MPU (Qualcomm QRB2210).

## Uploading:
Can be compiled and flashed via Arduino CLI or Arduino IDE targeting the Arduino UNO Q board.
