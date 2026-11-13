#include <cstdint>
#include <unity.h>

#include "hardware/calibration_session.h"

constexpr uint32_t kTimeout = CalibrationSession::kIdleTimeoutMs;

void test_closed_until_touched() {
  CalibrationSession session;
  TEST_ASSERT_FALSE(session.active(0));
  TEST_ASSERT_FALSE(session.active(5000));
}

void test_open_after_touch_until_timeout() {
  CalibrationSession session;
  session.touch(1000);
  TEST_ASSERT_TRUE(session.active(1000));
  TEST_ASSERT_TRUE(session.active(1000 + kTimeout - 1));
  TEST_ASSERT_FALSE(session.active(1000 + kTimeout));
}

void test_touch_extends_session() {
  CalibrationSession session;
  session.touch(0);
  session.touch(kTimeout - 10);
  TEST_ASSERT_TRUE(session.active(kTimeout + 100));
  TEST_ASSERT_FALSE(session.active(2 * kTimeout));
}

void test_end_closes_immediately() {
  CalibrationSession session;
  session.touch(0);
  session.end();
  TEST_ASSERT_FALSE(session.active(1));
}

void test_survives_millis_wrap() {
  CalibrationSession session;
  const uint32_t nearWrap = UINT32_MAX - 500;
  session.touch(nearWrap);
  TEST_ASSERT_TRUE(session.active(nearWrap + 1000));  // wrapped to 499
  TEST_ASSERT_FALSE(session.active(nearWrap + kTimeout + 1));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_closed_until_touched);
  RUN_TEST(test_open_after_touch_until_timeout);
  RUN_TEST(test_touch_extends_session);
  RUN_TEST(test_end_closes_immediately);
  RUN_TEST(test_survives_millis_wrap);
  return UNITY_END();
}
