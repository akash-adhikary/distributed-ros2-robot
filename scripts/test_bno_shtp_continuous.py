import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

const int PIN_SDA = 18; // A4
const int PIN_SCL = 19; // A5
const uint8_t BNO_ADDR = 0x4B;

int q_r = 10000;
int q_i = 0;
int q_j = 0;
int q_k = 0;
int sensor_active = 0;
int packet_count = 0;

int get_active() { return sensor_active; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }
int get_qj() { return q_j; }
int get_qk() { return q_k; }
int get_count() { return packet_count; }

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

void send_shtp_packet(uint8_t channel, uint8_t *payload, uint16_t len) {
  uint16_t total_len = len + 4;
  i2c_start();
  if (i2c_write_byte(BNO_ADDR << 1)) {
    i2c_write_byte(total_len & 0xFF);
    i2c_write_byte((total_len >> 8) & 0xFF);
    i2c_write_byte(channel);
    i2c_write_byte(0); // Seq
    for (uint16_t i = 0; i < len; i++) {
      i2c_write_byte(payload[i]);
    }
  }
  i2c_stop();
}

void enable_game_rotation_vector(uint32_t report_interval_us) {
  // SHTP command to enable report 0x08 (Game Rotation Vector) or 0x05 (Rotation Vector)
  uint8_t cmd[21] = {0};
  cmd[0] = 0xFD; // Set Feature Command
  cmd[1] = 0x05; // Feature Report ID: Rotation Vector (or 0x08 Game Rotation Vector)
  cmd[2] = 0x00; // Change sensitivity (0)
  cmd[3] = 0x00;
  cmd[4] = 0x00;
  cmd[5] = (report_interval_us) & 0xFF;
  cmd[6] = (report_interval_us >> 8) & 0xFF;
  cmd[7] = (report_interval_us >> 16) & 0xFF;
  cmd[8] = (report_interval_us >> 24) & 0xFF;
  send_shtp_packet(2, cmd, 21); // Control channel is 2
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/active", get_active);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);
  Bridge.provide("imu/count", get_count);
  
  i2c_start();
  if (i2c_write_byte(BNO_ADDR << 1)) {
    sensor_active = 1;
  }
  i2c_stop();
  
  delay(100);
  if (sensor_active) {
    enable_game_rotation_vector(20000); // 50Hz (20,000 us)
  }
}

void loop() {
  if (sensor_active) {
    // Read SHTP header
    i2c_start();
    if (i2c_write_byte((BNO_ADDR << 1) | 1)) {
      uint8_t len_lsb = i2c_read_byte(true);
      uint8_t len_msb = i2c_read_byte(true);
      uint8_t channel = i2c_read_byte(true);
      uint8_t seq     = i2c_read_byte(false);
      i2c_stop();
      
      uint16_t packet_len = (len_lsb | (len_msb << 8)) & ~0x8000;
      if (packet_len > 4 && packet_len < 128) {
        i2c_start();
        if (i2c_write_byte((BNO_ADDR << 1) | 1)) {
          uint8_t buf[128];
          for (int i = 0; i < packet_len; i++) {
            buf[i] = i2c_read_byte(i < (packet_len - 1));
          }
          i2c_stop();
          packet_count++;
          
          // Parse report if on Input Report channel 3
          if (channel == 3 && packet_len >= 19) {
            // Check report ID in body
            for (int i = 4; i < packet_len - 14; i++) {
              if (buf[i] == 0x05 || buf[i] == 0x08) { // Rotation Vector
                int16_t i_val = (int16_t)(buf[i+4] | (buf[i+5] << 8));
                int16_t j_val = (int16_t)(buf[i+6] | (buf[i+7] << 8));
                int16_t k_val = (int16_t)(buf[i+8] | (buf[i+9] << 8));
                int16_t r_val = (int16_t)(buf[i+10] | (buf[i+11] << 8));
                
                // Q-point scale factor for SHTP rotation vector is 2^14 = 16384
                q_i = (int)((float)i_val / 16384.0f * 10000.0f);
                q_j = (int)((float)j_val / 16384.0f * 10000.0f);
                q_k = (int)((float)k_val / 16384.0f * 10000.0f);
                q_r = (int)((float)r_val / 16384.0f * 10000.0f);
                break;
              }
            }
          }
        }
      }
    } else {
      i2c_stop();
    }
  }
  Bridge.update();
  delay(10);
}
SKETCH

echo "Compiling MCU sketch..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading MCU sketch..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_shtp.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_shtp.sh")
child.expect([r'ALL_DONE'], timeout=180)

child.sendline("exit")
child.expect(pexpect.EOF)
