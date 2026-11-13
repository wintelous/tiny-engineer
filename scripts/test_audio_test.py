"""Check actual diagnostic PCM: frequencies, full scale, automatic mute and failures."""

from array import array
from pathlib import Path
import math
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

ARDUINO = r'''
#pragma once
#include <cassert>
#include <cstdint>
#define PI 3.14159265358979323846
constexpr int OUTPUT=1, HIGH=1;
inline void pinMode(int pin, int mode) { assert(pin==5 && mode==OUTPUT); }
inline void digitalWrite(int pin, int level) { assert(pin==5 && level==HIGH); }
inline void delay(int) {}
struct SerialMock {
  void begin(int baud) { assert(baud==115200); }
  void setTxTimeoutMs(int) {}
  void println(const char*) {}
};
inline SerialMock Serial;
'''

I2S = r'''
#pragma once
#include <vector>
constexpr int I2S_MODE_STD=0, I2S_DATA_BIT_WIDTH_16BIT=16, I2S_SLOT_MODE_STEREO=2;
struct I2SClass {
  bool initOk=true, failWrite=false, ended=false;
  std::vector<int16_t> pcm;
  void setPins(int bclk,int ws,int data) { assert(bclk==2 && ws==3 && data==4); }
  bool begin(int mode,int rate,int bits,int slots) {
    assert(mode==I2S_MODE_STD && rate==16000 && bits==16 && slots==2);
    return initOk;
  }
  size_t write(const uint8_t* data,size_t size) {
    if (failWrite) return 0;
    const auto* samples=reinterpret_cast<const int16_t*>(data);
    pcm.insert(pcm.end(),samples,samples+size/sizeof(int16_t));
    return size;
  }
  bool end() { ended=true; return true; }
};
'''

CHECK = r'''
#include <fstream>
#include "examples/audio-test/main.cpp"
int main(int argc,char** argv) {
  assert(argc==2);
  setup(); assert(audioReady);
  for(int i=0;i<1200;i++) loop();
  assert(frameCursor==0 && completedCycles==3 && audio.pcm.size()==384000);
  std::ofstream out(argv[1],std::ios::binary);
  out.write(reinterpret_cast<const char*>(audio.pcm.data()),audio.pcm.size()*sizeof(int16_t));
  audio.failWrite=true; loop(); assert(!audioReady && audio.ended);
  const auto size=audio.pcm.size(); loop(); assert(audio.pcm.size()==size);
  audio.initOk=false; setup(); assert(!audioReady);
}
'''


def main():
    with tempfile.TemporaryDirectory(prefix="tiny-audio-check-") as tmp:
        directory = Path(tmp)
        (directory / "Arduino.h").write_text(ARDUINO)
        (directory / "ESP_I2S.h").write_text(I2S)
        cpp = directory / "check.cpp"
        cpp.write_text(CHECK)
        exe, pcm = directory / "check", directory / "pcm.bin"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        f"-I{directory}", f"-I{ROOT}", f"-I{ROOT / 'include'}",
                        str(cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe), str(pcm)], check=True)
        samples = array("h", pcm.read_bytes())
    assert samples[::2] == samples[1::2], "Stereo channels differ"
    mono = samples[::2]
    assert 32000 <= max(abs(value) for value in mono) <= 32767
    for cycle in range(3):
        offset = cycle * 48000
        for start, hz in [(0, 500), (1600, 1000)]:
            note = mono[offset + start:offset + start + 1600]
            assert abs(sum(note) / len(note)) < 1, "Unexpected DC offset"
            projection = sum(value * math.sin(2 * math.pi * hz * (start + i) / 16000)
                             for i, value in enumerate(note)) * 2 / len(note)
            assert 32740 < projection < 32780, (hz, projection)
        assert all(value == 0 for value in mono[offset + 3200:offset + 48000])
    assert all(value == 0 for value in mono[144000:]), "Automatic mute failed"
    print("PASS: full-scale 100 ms stereo tones, zero-DC, three rounds then silence, failure stops")


if __name__ == "__main__":
    main()
