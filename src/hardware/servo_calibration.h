#pragma once

// Per-joint calibration outside setup AP mode (POST /servo/calibrate).
// While a session is active, animations are refused and servo PWM stays on,
// so nothing but calibration moves the joints.

bool servoCalibrationActive();

// Opens or refreshes the session. Opening it parks the idle pose first.
void servoCalibrationTouch();

// Closes an active session and returns to the idle pose inside the saved ranges.
void servoCalibrationEnd();
