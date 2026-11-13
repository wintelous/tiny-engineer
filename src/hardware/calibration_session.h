#pragma once

#include <cstdint>

// Normal-mode servo calibration stays open while moves keep arriving and
// closes on its own after a quiet spell, so a closed browser tab never leaves
// the robot frozen. Unsigned subtraction keeps it right across millis() wrap.
class CalibrationSession {
 public:
  static constexpr uint32_t kIdleTimeoutMs = 120000;

  void touch(uint32_t nowMs) {
    open_ = true;
    lastMs_ = nowMs;
  }

  void end() { open_ = false; }

  bool active(uint32_t nowMs) const { return open_ && nowMs - lastMs_ < kIdleTimeoutMs; }

 private:
  bool open_ = false;
  uint32_t lastMs_ = 0;
};
