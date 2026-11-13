"""Compile the actual RGB controller with fake GPIO and check its PWM outputs."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]

STUBS = {
    "Arduino.h": """
#pragma once
#include <cstdint>
void analogWrite(uint8_t pin, int level);
inline uint32_t millis() { return 0; }
inline void delay(uint32_t) {}
struct SerialStub {
  template<typename T> void print(T) {}
  template<typename T> void println(T) {}
  void println() {}
  void flush() {}
};
inline SerialStub Serial;
""",
    "network/wifi_connect.h": """
#pragma once
inline bool provisioning = false;
inline bool wifiProvisioningMode() { return provisioning; }
""",
    "serial_log.h": """
#pragma once
template<typename... T> void serialLogPrintln(T...) {}
""",
    "settings/settings.h": """
#pragma once
#include <string_view>
inline const char* savedOrder = "RGB";
inline const char* settingsRgbOrder() { return savedOrder; }
inline bool settingsValidateRgbOrder(const char* order) {
  if (!order) return false;
  for (auto valid : {"RGB", "RBG", "GRB", "GBR", "BRG", "BGR"}) {
    if (std::string_view(order) == valid) return true;
  }
  return false;
}
""",
}

CHECK = r"""
#include <array>
#include <cassert>
#include <cstdio>
#include "hardware/rgb.cpp"

std::array<int, 22> output{};
int writes = 0;
void analogWrite(uint8_t pin, int level) {
  assert(pin == 6 || pin == 7 || pin == 10);
  assert(level >= 0 && level <= 255);
  output[pin] = level;
  ++writes;
}
AnimationId getAnimation() { return AnimationId::None; }
void expect(int r, int g, int b) {
  if (output[6] != r || output[7] != g || output[10] != b) {
    std::fprintf(stderr, "Expected %d,%d,%d; got %d,%d,%d\n",
                 r, g, b, output[6], output[7], output[10]);
  }
  assert(output[6] == r && output[7] == g && output[10] == b);
}
int main() {
  static_assert(RGB_RED_PIN == 6 && RGB_GREEN_PIN == 7 && RGB_BLUE_PIN == 10);
  static_assert(I2C_SDA == 0 && I2C_SCL == 1 && PCA9685_OE_PIN == 5);
  static_assert(I2S_BCLK == 2 && I2S_LRC == 3 && I2S_DIN == 4);
  const char* orders[] = {"RGB", "RBG", "GRB", "GBR", "BRG", "BGR"};
  const int levels[][3] = {{11,22,33},{11,33,22},{22,11,33},
                           {22,33,11},{33,11,22},{33,22,11}};
  for (int i = 0; i < 6; ++i) {
    savedOrder = orders[i];
    writes = 0;
    setRgb(11, 22, 33);
    assert(writes == 3);
    expect(levels[i][0], levels[i][1], levels[i][2]);
  }
  savedOrder = "GRB";
  rgbSetupHoldWireByte(0); expect(255, 0, 0);
  rgbSetupHoldWireByte(1); expect(0, 255, 0);
  rgbSetupHoldWireByte(2); expect(0, 0, 255);
  rgbSetupHoldLogical(255, 0, 0, "BRG"); expect(0, 255, 0);
  rgbSetupHoldLogical(255, 0, 0, "bad"); expect(0, 255, 0);
  rgbSetupHoldLogical(255, 0, 0, nullptr); expect(0, 255, 0);
  savedOrder = "RGB";
  provisioning = true;
  rgbSetupRelease(); expect(0, 0, 64);
  rgbSetupHoldWireByte(0);
  updateRgb(0); expect(255, 0, 0);
  rgbSetupRelease(); expect(0, 0, 64);
  provisioning = false;
  updateRgb(0);
  setRgb(0, 0, 0); expect(0, 0, 0);
  setRgbForAnimation(AnimationId::Typing, 0);
  updateRgb(500); expect(127, 127, 127);
  updateRgb(1000); expect(255, 255, 255);
  setRgbForAnimation(AnimationId::Attention, 1000); expect(26, 0, 0);
  updateRgb(1500); expect(255, 0, 0);
  runRgbTest(); expect(0, 0, 0);
}
"""


def main():
    assert 'SETTINGS_DEFAULT_RGB_ORDER = "RGB"' in (
        ROOT / "src/settings/settings.h"
    ).read_text()
    with tempfile.TemporaryDirectory(prefix="tiny-supermini-rgb-") as tmp:
        directory = Path(tmp)
        for name, content in STUBS.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        check = directory / "check.cpp"
        check.write_text(CHECK)
        executable = directory / "check"
        subprocess.run([
            "g++", "-std=c++17", "-DTE_BOARD_SUPERMINI", "-Wall", "-Wextra", "-Werror",
            f"-I{directory}", f"-I{ROOT / 'src'}", f"-I{ROOT / 'include'}",
            str(check), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)
    print("PASS: RGB pins, six mappings, setup previews/release, fades, pulses and off")


if __name__ == "__main__":
    main()
