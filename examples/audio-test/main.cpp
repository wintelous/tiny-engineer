#include <Arduino.h>
#include <ESP_I2S.h>
#include <cmath>

#include "pins.h"

constexpr uint32_t kTestRate = 16000;
constexpr uint32_t kBlockFrames = 160;
constexpr uint32_t kNoteFrames = 1600;
constexpr uint32_t kCycleFrames = 48000;
constexpr int16_t kAmplitude = 32767;

static_assert(I2S_BCLK == 2 && I2S_LRC == 3 && I2S_DIN == 4 && PCA9685_OE_PIN == 5);
static_assert(kTestRate == 16000 && kAmplitude > 0 && kAmplitude <= 32767);
static_assert(kNoteFrames % kBlockFrames == 0 && kCycleFrames % kBlockFrames == 0);

I2SClass audio;
bool audioReady = false;
uint32_t frameCursor = 0;
uint8_t completedCycles = 0;

void setup() {
  pinMode(PCA9685_OE_PIN, OUTPUT);
  digitalWrite(PCA9685_OE_PIN, HIGH);
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);
  delay(1000);
  audio.setPins(I2S_BCLK, I2S_LRC, I2S_DIN);
  audioReady = audio.begin(I2S_MODE_STD, kTestRate, I2S_DATA_BIT_WIDTH_16BIT,
                           I2S_SLOT_MODE_STEREO);
  Serial.println(audioReady ? "AUDIO READY: 16000 Hz, full-scale short beeps; OE HIGH" :
                              "AUDIO FAIL: I2S initialization");
}

void loop() {
  if (!audioReady) {
    delay(100);
    return;
  }
  int16_t samples[kBlockFrames * 2];
  for (uint32_t i = 0; i < kBlockFrames; i++) {
    const uint32_t position = frameCursor + i;
    const int hz = completedCycles >= 3 ? 0 :
        position < kNoteFrames ? 500 : position < 2 * kNoteFrames ? 1000 : 0;
    const int16_t value = static_cast<int16_t>(
        kAmplitude * sinf(2.0f * PI * hz * position / kTestRate));
    samples[i * 2] = value;
    samples[i * 2 + 1] = value;
  }
  if (audio.write(reinterpret_cast<const uint8_t*>(samples), sizeof(samples)) != sizeof(samples)) {
    audio.end();
    audioReady = false;
    Serial.println("AUDIO FAIL: incomplete I2S write; stopped");
    return;
  }
  frameCursor = (frameCursor + kBlockFrames) % kCycleFrames;
  if (frameCursor == 0 && completedCycles < 3) {
    completedCycles++;
    Serial.println(completedCycles == 3 ? "AUDIO DONE: muted after three rounds" :
                                         "AUDIO: full-scale beep pair completed");
  }
}
