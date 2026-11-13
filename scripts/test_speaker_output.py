"""Check real speaker conversion: supported clock, PCM timing, volume and tones."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

PRELUDE = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <vector>
#include "pins.h"
using std::min;
constexpr double PI=3.14159265358979323846;
uint8_t volume=100;
uint8_t settingsVolume() { return volume; }
struct SpeakerMock {
  std::vector<int16_t> pcm;
  size_t write(const uint8_t* data,size_t size) {
    assert(size%8==0 && size<=256*8);
    const auto* samples=reinterpret_cast<const int16_t*>(data);
    pcm.insert(pcm.end(),samples,samples+size/2);
    return size;
  }
} I2S;
'''

CHECK = r'''
int main() {
  static_assert(SAMPLE_RATE==22050 && I2S_SAMPLE_RATE==44100);
  std::vector<int16_t> input(601);
  for(size_t i=0;i<input.size();i++) input[i]=i%2 ? -32768 : 32767;
  writeMonoToSpeaker(input.data(),input.size());
  assert(I2S.pcm.size()==input.size()*4);
  for(size_t i=0;i<input.size();i++)
    for(size_t slot=0;slot<4;slot++) assert(I2S.pcm[i*4+slot]==input[i]);
  const double inputSeconds=double(input.size())/SAMPLE_RATE;
  const double outputSeconds=double(I2S.pcm.size()/2)/I2S_SAMPLE_RATE;
  assert(std::abs(inputSeconds-outputSeconds)<1e-12);
  volume=50; I2S.pcm.clear(); writeMonoToSpeaker(input.data(),input.size());
  for(size_t i=0;i<input.size();i++)
    for(size_t slot=0;slot<4;slot++) assert(I2S.pcm[i*4+slot]==input[i]/2);
  volume=0; I2S.pcm.clear(); writeMonoToSpeaker(input.data(),input.size());
  for(int sample:I2S.pcm) assert(sample==0);
  volume=100; I2S.pcm.clear(); playTone(1000,200);
  assert(I2S.pcm.size()==17640); // 200 ms of 44.1 kHz stereo output
  const auto full=I2S.pcm;
  int peak=0;
  double projection=0;
  for(size_t frame=0;frame<full.size()/2;frame++) {
    const int sample=full[frame*2];
    peak=std::max(peak,std::abs(sample));
    assert(full[frame*2]==full[frame*2+1]);
    assert(full[frame*2]==full[(frame/2)*4]);
    projection+=sample*std::sin(2*PI*1000*frame/I2S_SAMPLE_RATE);
  }
  assert(peak>32700 && peak<=32767);
  projection*=2.0/(full.size()/2);
  assert(projection>32500 && projection<32768); // correct physical frequency
  volume=50; I2S.pcm.clear(); playTone(1000,200);
  assert(I2S.pcm.size()==full.size());
  for(size_t i=0;i<full.size();i++) assert(I2S.pcm[i]==full[i]/2);
  I2S.pcm.clear(); playSilence(200); assert(I2S.pcm.size()==17640);
  for(int sample:I2S.pcm) assert(sample==0);
}
'''


def main():
    source = (ROOT / "src/audio/audio.cpp").read_text()
    start = source.index("void writeMonoToSpeaker(")
    end = source.index("void stopAllWavPlayback(", start)
    with tempfile.TemporaryDirectory(prefix="tiny-speaker-check-") as tmp:
        cpp, exe = Path(tmp) / "check.cpp", Path(tmp) / "check"
        cpp.write_text(PRELUDE + source[start:end] + CHECK)
        subprocess.run(["g++", "-std=c++17", "-DTE_BOARD_SUPERMINI", "-Wall", "-Wextra", "-Werror",
                        f"-I{ROOT / 'include'}", str(cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print("PASS: 44.1 kHz output, unchanged PCM duration/pitch, full-scale and single volume scaling, stereo and silence")


if __name__ == "__main__":
    main()
