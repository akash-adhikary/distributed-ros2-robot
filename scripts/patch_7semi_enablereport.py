import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""python3 -c "
with open('/home/arduino/Arduino/libraries/7Semi_BNO08x/src/7Semi_BNO08x.cpp', 'r') as f:
    c = f.read()

old_func = '''bool BNO08x_7Semi::enableReport(uint8_t reportId, uint32_t intervalMs)
{
  if (!writeSetFeature_(reportId, intervalMs, SHTP_CH_CTRL, 0xFD))
    return false;

  if (!waitForSetFeatureResponse(reportId, 100))
  {
    if (!writeSetFeature_(reportId, intervalMs, SHTP_CH_CTRL, 0xFD))
      return false;
    if (!waitForSetFeatureResponse(reportId, 100))
      return false;
  }

  return true;
}'''

new_func = '''bool BNO08x_7Semi::enableReport(uint8_t reportId, uint32_t intervalMs)
{
  writeSetFeature_(reportId, intervalMs, SHTP_CH_CTRL, 0xFD);
  delay(10);
  writeSetFeature_(reportId, intervalMs, SHTP_CH_CTRL, 0xFD);
  return true;
}'''

if old_func in c:
    c = c.replace(old_func, new_func)
    with open('/home/arduino/Arduino/libraries/7Semi_BNO08x/src/7Semi_BNO08x.cpp', 'w') as f:
        f.write(c)
    print('PATCHED_SUCCESSFULLY')
else:
    print('COULD_NOT_FIND_OLD_FUNC')
"
""")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
