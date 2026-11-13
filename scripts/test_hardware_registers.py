"""Check the bench program's real register-read code with auto-increment off."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def main():
    source = (ROOT / "examples/hardware-test/main.cpp").read_text()
    body = source.split("  if (found[PCA9685_ADDRESS]) {", 1)[1].split(
        '  } else {\n    Serial.println("PCA FAIL: no device', 1
    )[0]
    helper = ""
    if "int readPcaRegister(" in source:
        helper = source[source.index("int readPcaRegister("):source.index("\nvoid setup()")]
    harness = r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <string>
constexpr uint8_t PCA9685_ADDRESS = 0x40;
struct WireMock {
  uint8_t pointer = 0;
  int writes = 0;
  bool nack = false;
  bool shortRead = false;
  void beginTransmission(uint8_t address) {
    assert(address == 0x40);
    writes = 0;
  }
  void write(uint8_t value) {
    assert(++writes == 1 && value <= 1); // Register pointer only; no PWM writes.
    pointer = value;
  }
  int endTransmission(bool stop) { assert(!stop); return nack ? 2 : 0; }
  int requestFrom(uint8_t address, uint8_t count) {
    assert(address == 0x40);
    return shortRead ? 0 : count;
  }
  int read() { return pointer == 0 ? 0x11 : 0x04; } // AI disabled: never advance.
} Wire;
struct SerialMock {
  template<typename... T> void printf(const char* format, T... values) {
    std::printf(format, values...);
  }
  void println(const char* text) { std::puts(text); }
} Serial;
'''
    harness += helper + "\nvoid probe() {\n" + body + "\n}\n"
    harness += r'''
int main() {
  std::puts("NORMAL"); probe();
  std::puts("NACK"); Wire.nack = true; probe();
  std::puts("SHORT"); Wire.nack = false; Wire.shortRead = true; probe();
}
'''
    with tempfile.TemporaryDirectory(prefix="tiny-pca-registers-") as tmp:
        cpp = Path(tmp) / "check.cpp"
        exe = Path(tmp) / "check"
        cpp.write_text(harness)
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        str(cpp), "-o", str(exe)], check=True)
        result = subprocess.check_output([str(exe)], text=True)
    normal, errors = result.split("NACK\n", 1)
    assert "MODE1=0x11 MODE2=0x04" in normal, result
    assert "PCA PASS" not in errors and errors.count("PCA FAIL") == 2, result
    print("PASS: distinct MODE1/MODE2 with AI off; NACK/short reads fail; no PWM writes")


if __name__ == "__main__":
    main()
