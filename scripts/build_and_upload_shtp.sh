set -e
cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

const int PIN_SDA = 18; // A4
const int PIN_SCL = 19; // A5
const uint8_t BNO_ADDR = 0x4B;

int q_r = 10000, q_i = 0, q_j = 0, q_k = 0;
int last_chan = 0, last_len = 0, pkt_count = 0;

int get_chan() { return last_chan; }
int get_len() { return last_len; }
int get_count() { return pkt_count; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }
int get_qj() { return q_j; }
int get_qk() { return q_k; }

void i2c_start() {
  pinMode(PIN_SDA, OUTPUT);
  pinMode(PIN_SCL, OUTPUT);
  digitalWrite(PIN_SDA, HIGH);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  digitalWrite(PIN_SDA, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(5);
}

void i2c_stop() {
  pinMode(PIN_SDA, OUTPUT);
  digitalWrite(PIN_SDA, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  digitalWrite(PIN_SDA, HIGH);
  delayMicroseconds(5);
}

bool i2c_write_byte(uint8_t b) {
  pinMode(PIN_SDA, OUTPUT);
  for (int i = 7; i >= 0; i--) {
    digitalWrite(PIN_SDA, (b & (1 << i)) ? HIGH : LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_SCL, HIGH);
    delayMicroseconds(5);
    digitalWrite(PIN_SCL, LOW);
    delayMicroseconds(2);
  }
  pinMode(PIN_SDA, INPUT_PULLUP);
  delayMicroseconds(2);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  bool ack = (digitalRead(PIN_SDA) == LOW);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(2);
  return ack;
}

uint8_t i2c_read_byte(bool ack) {
  pinMode(PIN_SDA, INPUT_PULLUP);
  uint8_t b = 0;
  for (int i = 7; i >= 0; i--) {
    digitalWrite(PIN_SCL, HIGH);
    delayMicroseconds(5);
    if (digitalRead(PIN_SDA) == HIGH) b |= (1 << i);
    digitalWrite(PIN_SCL, LOW);
    delayMicroseconds(3);
  }
  pinMode(PIN_SDA, OUTPUT);
  digitalWrite(PIN_SDA, ack ? LOW : HIGH);
  delayMicroseconds(2);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(2);
  return b;
}

void send_shtp(uint8_t chan, uint8_t *payload, uint16_t len) {
  uint16_t total = len + 4;
  i2c_start();
  if (i2c_write_byte(BNO_ADDR << 1)) {
    i2c_write_byte(total & 0xFF);
    i2c_write_byte((total >> 8) & 0xFF);
    i2c_write_byte(chan);
    i2c_write_byte(0);
    for (uint16_t i = 0; i < len; i++) i2c_write_byte(payload[i]);
  }
  i2c_stop();
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/chan", get_chan);
  Bridge.provide("imu/len", get_len);
  Bridge.provide("imu/count", get_count);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);

  // Set Feature Command: Enable Rotation Vector (0x05) at 50Hz (20000 us)
  uint8_t cmd[21] = {0};
  cmd[0] = 0xFD;
  cmd[1] = 0x05;
  cmd[5] = 0x20; cmd[6] = 0x4E;
  send_shtp(2, cmd, 21);
}

void loop() {
  i2c_start();
  if (i2c_write_byte((BNO_ADDR << 1) | 1)) {
    uint8_t lsb = i2c_read_byte(true);
    uint8_t msb = i2c_read_byte(true);
    uint8_t ch  = i2c_read_byte(true);
    uint8_t seq = i2c_read_byte(false);
    i2c_stop();

    uint16_t plen = (lsb | (msb << 8)) & ~0x8000;
    if (plen > 4 && plen < 128) {
      last_chan = ch;
      last_len = plen;
      pkt_count++;

      i2c_start();
      if (i2c_write_byte((BNO_ADDR << 1) | 1)) {
        uint8_t buf[128];
        for (int i = 0; i < plen; i++) {
          buf[i] = i2c_read_byte(i < (plen - 1));
        }
        i2c_stop();

        for (int i = 4; i < plen - 14; i++) {
          if (buf[i] == 0x05 || buf[i] == 0x08) {
            int16_t ival = (int16_t)(buf[i+4] | (buf[i+5] << 8));
            int16_t jval = (int16_t)(buf[i+6] | (buf[i+7] << 8));
            int16_t kval = (int16_t)(buf[i+8] | (buf[i+9] << 8));
            int16_t rval = (int16_t)(buf[i+10] | (buf[i+11] << 8));

            q_i = (int)((float)ival / 16384.0f * 10000.0f);
            q_j = (int)((float)jval / 16384.0f * 10000.0f);
            q_k = (int)((float)kval / 16384.0f * 10000.0f);
            q_r = (int)((float)rval / 16384.0f * 10000.0f);
            break;
          }
        }
      }
    }
  } else {
    i2c_stop();
  }
  Bridge.update();
  delay(10);
}
SKETCH

echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "BUILD_DONE"
