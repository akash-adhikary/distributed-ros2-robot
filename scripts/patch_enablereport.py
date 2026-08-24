import re

with open('/home/arduino/Arduino/libraries/7Semi_BNO08x/src/7Semi_BNO08x.cpp', 'r') as f:
    c = f.read()

# Replace enableReport definition
pattern = r'bool BNO08x_7Semi::enableReport\(uint8_t reportId, uint32_t intervalMs\)\s*\{[\s\S]*?\n\}'
replacement = '''bool BNO08x_7Semi::enableReport(uint8_t reportId, uint32_t intervalMs)
{
  writeSetFeature_(reportId, intervalMs, SHTP_CH_CTRL, 0xFD);
  delay(5);
  return true;
}'''

new_c = re.sub(pattern, replacement, c)
with open('/home/arduino/Arduino/libraries/7Semi_BNO08x/src/7Semi_BNO08x.cpp', 'w') as f:
    f.write(new_c)

print("PATCH_COMPLETE")
