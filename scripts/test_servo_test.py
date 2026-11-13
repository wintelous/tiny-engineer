"""Check the actual servo diagnostic's startup, parser, timeout and I2C failures."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

ARDUINO = r'''
#pragma once
#include <cassert>
#include <cstdint>
#include <deque>
#include <string>
constexpr int OUTPUT=1, HIGH=1, LOW=0;
inline uint32_t now=0;
inline int oe=HIGH, enables=0;
inline uint32_t millis() { return now; }
inline void delay(uint32_t ms) { now+=ms; }
inline void pinMode(int pin,int mode) { assert(pin==5 && mode==OUTPUT); }
void digitalWrite(int pin,int level);
struct SerialMock {
  std::deque<char> rx;
  void begin(int baud) { assert(baud==115200); }
  void setTxTimeoutMs(int) {}
  void println(const char*) {}
  template<class... Args> void printf(const char*,Args...) {}
  int available() { return rx.size(); }
  char read() { char ch=rx.front(); rx.pop_front(); return ch; }
};
inline SerialMock Serial;
'''

WIRE = r'''
#pragma once
struct WireMock {
  bool ok=true;
  bool begin(int sda,int scl,int hz) { assert(sda==0 && scl==1 && hz==100000); return ok; }
  void setTimeOut(int ms) { assert(ms==100); }
};
inline WireMock Wire;
'''

PWM = r'''
#pragma once
#include <array>
struct Adafruit_PWMServoDriver {
  std::array<int,16> counts{};
  bool ok=true,failOff=false,failPulse=false;
  explicit Adafruit_PWMServoDriver(int address) { assert(address==0x40); }
  bool begin() { return ok; }
  void setPWMFreq(int hz) { assert(hz==50); }
  int setPWM(int channel,int on,int off) {
    assert(oe==HIGH && channel>=0 && channel<16 && on==0);
    assert(off==4096 || (off>=297 && off<=317));
    if ((off==4096 && failOff) || (off!=4096 && failPulse)) return 1;
    counts[channel]=off;
    return 0;
  }
};
'''

CHECK = r'''
#include "examples/servo-test/main.cpp"
void digitalWrite(int pin,int level) {
  assert(pin==5);
  if(level==LOW) {
    int active=0;
    for(int value:pwm.counts) if(value!=4096) { assert(value>=297 && value<=317); active++; }
    assert(active==1);
    enables++;
  }
  oe=level;
}
void send(const std::string& line) {
  for(char ch:line) Serial.rx.push_back(ch);
  while(Serial.available()) loop();
}
void off() {
  assert(oe==HIGH && !outputsEnabled);
  for(int value:pwm.counts) assert(value==4096);
}
int main() {
  setup(); assert(controllerReady && enables==0); off();
  send("STATUS\n"); assert(enables==0); off();
  send("C0\r\n"); assert(outputsEnabled && pwm.counts[0]==307);
  now+=1999; loop(); assert(outputsEnabled);
  now++; loop(); off();
  send("-1\n"); assert(pwm.counts[1]==297);
  send("+1\n"); assert(pwm.counts[1]==317);
  send("OFF\n"); off();
  send("C4\n"); assert(pwm.counts[4]==307);
  send("OFF\n"); off();
  const int before=enables;
  send("C5\nC00\nc0\n C0\nC0garbagegarbage\n\n");
  send(std::string("C0\0\n",4)); assert(enables==before); off();
  now=UINT32_MAX-100; send("C0\n"); now+=2000; loop(); off();
  send("C0\n"); now+=2000;
  for(int i=0;i<1000;i++) Serial.rx.push_back('x');
  loop(); off(); assert(Serial.rx.size()==968);
  Serial.rx.clear(); send("\n");
  pwm.failPulse=true; send("C0\n"); assert(!controllerReady); off();
  pwm.failPulse=false; setup(); assert(controllerReady); off();
  pwm.failOff=true; send("C0\n"); assert(!controllerReady && oe==HIGH && !outputsEnabled);
  pwm.failOff=false; pwm.ok=false; setup(); assert(!controllerReady && oe==HIGH);
  pwm.ok=true; Wire.ok=false; setup(); assert(!controllerReady && oe==HIGH);
}
'''


def main():
    with tempfile.TemporaryDirectory(prefix="tiny-servo-check-") as tmp:
        directory = Path(tmp)
        for name, source in [("Arduino.h", ARDUINO), ("Wire.h", WIRE),
                             ("Adafruit_PWMServoDriver.h", PWM), ("check.cpp", CHECK)]:
            (directory / name).write_text(source)
        exe = directory / "check"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        f"-I{directory}", f"-I{ROOT}", f"-I{ROOT / 'include'}",
                        str(directory / "check.cpp"), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print("PASS: outputs off at startup, one channel, narrow pulses, parser, timeout and I2C failures")


if __name__ == "__main__":
    main()
