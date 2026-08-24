import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'HEOF' > /home/arduino/Arduino/libraries/7Semi_BNO08x/src/BnoI2CBus.h
#pragma once
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

    // 1. Read SHTP 4-byte header
    uint8_t hdr_cnt = w->requestFrom((uint8_t)addr, (uint8_t)4);
    if (hdr_cnt < 4) return 0;

    buf[0] = w->read();
    buf[1] = w->read();
    buf[2] = w->read();
    buf[3] = w->read();

    uint16_t len = (uint16_t(buf[0]) | (uint16_t(buf[1]) << 8)) & 0x7FFF;
    if (len < 4 || len > cap) return 4;

    // 2. Read remainder of payload in standard 32-byte chunks
    uint16_t remaining = len - 4;
    uint16_t offset = 4;

    while (remaining > 0) {
      uint8_t chunk = (remaining > 28) ? 28 : (uint8_t)remaining;
      uint8_t read_bytes = w->requestFrom((uint8_t)addr, chunk);
      if (read_bytes == 0) break;
      for (uint8_t i = 0; i < read_bytes; i++) {
        if (offset < cap) buf[offset++] = w->read();
        else w->read();
      }
      remaining -= read_bytes;
    }

    return offset;
  }
};
HEOF
""")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
