#include "hardware/servo_calibration.h"

#include <Arduino.h>

#include "animation.h"
#include "hardware/calibration_session.h"
#include "serial_log.h"

namespace {

CalibrationSession g_session;

}  // namespace

bool servoCalibrationActive() {
  return g_session.active(millis());
}

void servoCalibrationTouch() {
  if (!servoCalibrationActive()) {
    // Park before the gate closes: the idle pose is the last animation applied.
    setAnimationImmediately(AnimationId::None);
    serialLogPrintln("[calib] session open");
  }

  g_session.touch(millis());
}

void servoCalibrationEnd() {
  if (!servoCalibrationActive()) {
    g_session.end();
    return;
  }

  g_session.end();
  serialLogPrintln("[calib] session closed");
  setAnimationImmediately(AnimationId::None);
}
