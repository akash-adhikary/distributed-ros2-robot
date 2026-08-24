new_bno_bus = '''#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "BnoBus.h"

struct BnoI2CBus : public BnoBus
{
  TwoWire *w;
  int sda;
  int scl;
  uint8_t addr;
  uint32_t clk;
  int intn;
  int rst;

  BnoI2CBus(TwoWire &wire = Wire,
            int sdaPin = -1,
            int sclPin = -1,
            uint8_t i2cAddr = 0x4B,
            uint32_t clock = 100000,
            int intnPin = -1,
            int rstPin = -1)
      : w(&wire),
        sda(sdaPin),
        scl(sclPin),
        addr(i2cAddr),
        clk(clock),
        intn(intnPin),
        rst(rstPin)
  {}

  bool begin() override
  {
    if (!w) return false;
    w->begin();
    if (intn >= 0) pinMode(intn, INPUT_PULLUP);
    if (rst >= 0) {
      pinMode(rst, OUTPUT);
      digitalWrite(rst, HIGH);
      delay(5);
      digitalWrite(rst, LOW);
      delay(10);
      digitalWrite(rst, HIGH);
      delay(300);
    }
    return true;
  }

  bool tx(const uint8_t *data, size_t n) override
  {
    if (!w || !data || n == 0) return false;
    w->beginTransmission(addr);
    w->write(data, n);
    return (w->endTransmission() == 0);
  }

  int rx(uint8_t *buf, size_t cap) override
  {
    if (!w || !buf || cap < 4) return 0;

    // In STM32 Zephyr Wire, max single requestFrom is 32 bytes
    uint8_t req = (cap > 32) ? 32 : (uint8_t)cap;
    uint8_t n = w->requestFrom((uint8_t)addr, req);
    if (n < 4) return 0;

    for (uint8_t i = 0; i < n; i++) {
      buf[i] = w->read();
    }

    uint16_t len = (uint16_t(buf[0]) | (uint16_t(buf[1]) << 8)) & 0x7FFF;
    if (len > n) len = n;
    return len;
  }
};
'''

with open('/home/arduino/Arduino/libraries/7Semi_BNO08x/src/BnoI2CBus.h', 'w') as f:
    f.write(new_bno_bus)

print("PERFECT_BNO_BUS_WRITTEN")
