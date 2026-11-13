#include <Arduino.h>
#include <ESP_I2S.h>
#include <FS.h>
#include <LittleFS.h>
#include <math.h>

#include "animation.h"
#include "api/busy.h"
#include "audio/audio_cues.h"
#include "audio/wav_stream.h"
#include "extensions/push_button_sfx.h"
#include "pins.h"
#include "display/oled.h"
#include "settings/settings.h"
#include "audio/audio.h"
#include "serial_log.h"

I2SClass I2S;

namespace {

bool audioStorageReady = false;

constexpr const char* kAudioPartition = "spiffs";

void logAudioStorageContents() {
  File root = LittleFS.open("/");

  if (!root || !root.isDirectory()) {
    serialLogPrintln("LittleFS root unavailable");
    return;
  }

  serialLogPrintln("LittleFS files:");

  File entry = root.openNextFile();

  while (entry) {
    serialLogPrint("  ");
    serialLogPrintln(entry.name());
    entry.close();
    entry = root.openNextFile();
  }

  root.close();
}

bool playWavBlocking(
  WavClip clip,
  const char* line2
) {
  const char* line1 = wavClipOledTitle(clip);

  showOledText(line1, line2);

  if (!wavStreamStart(clip)) {
    showOledText(line1, "Failed");
    return false;
  }

  while (wavStreamUpdate()) {
    delay(1);
  }

  showOledText(line1, "OK");
  return true;
}

}  // namespace

bool initAudioStorage() {
  if (audioStorageReady) {
    return true;
  }

  audioStorageReady = LittleFS.begin(
    false,
    "/littlefs",
    10,
    kAudioPartition
  );

  if (!audioStorageReady) {
    serialLogPrintln("LittleFS mount failed (run: pio run -t uploadfs)");
    return false;
  }

  for (uint8_t i = 0; i < kWavClipCount; i++) {
    const WavClip clip = static_cast<WavClip>(i);
    const char* path = wavClipPath(clip);

    if (!LittleFS.exists(path)) {
      serialLogPrint(path);
      serialLogPrintln(" not on LittleFS");
      logAudioStorageContents();
    }
  }

  loadAudioCues();
  return true;
}

void writeMonoToSpeaker(const int16_t* samples, size_t count, uint8_t volume) {
  constexpr size_t FRAMES = 256;

  constexpr size_t SLOTS = 2 * I2S_FRAME_REPEAT;  // stereo, each frame I2S_FRAME_REPEAT times

  int16_t buffer[FRAMES * SLOTS];

  while (count > 0) {
    const size_t framesThisTime = count < FRAMES ? count : FRAMES;

    for (size_t i = 0; i < framesThisTime; i++) {
      int32_t scaled = (static_cast<int32_t>(samples[i]) * volume) / 100;

      if (scaled > 32767) {
        scaled = 32767;
      } else if (scaled < -32768) {
        scaled = -32768;
      }

      for (size_t slot = 0; slot < SLOTS; slot++) {
        buffer[i * SLOTS + slot] = static_cast<int16_t>(scaled);
      }
    }

    I2S.write(
      reinterpret_cast<uint8_t*>(buffer),
      framesThisTime * SLOTS * sizeof(int16_t)
    );

    samples += framesThisTime;
    count -= framesThisTime;
  }
}

void writeMonoToSpeaker(const int16_t* samples, size_t count) {
  writeMonoToSpeaker(samples, count, settingsVolume());
}

void playTone(
  float frequency,
  int durationMs
) {
  constexpr int FRAMES = 512;

  int16_t buffer[FRAMES];

  float phase = 0.0f;

  const float phaseStep =
    2.0f * PI * frequency / SAMPLE_RATE;

  // writeMonoToSpeaker applies the volume.
  const float amplitude = 32767.0f;

  const int totalFrames =
    SAMPLE_RATE * durationMs / 1000;

  int framesPlayed = 0;

  while (framesPlayed < totalFrames) {
    const int framesThisTime =
      min(
        FRAMES,
        totalFrames - framesPlayed
      );

    for (int i = 0; i < framesThisTime; i++) {
      const int16_t sample =
        (int16_t)(
          sin(phase) * amplitude
        );

      phase += phaseStep;

      if (phase >= 2.0f * PI) {
        phase -= 2.0f * PI;
      }

      buffer[i] = sample;
    }

    writeMonoToSpeaker(buffer, framesThisTime);

    framesPlayed += framesThisTime;
  }
}

void playSilence(int durationMs) {
  constexpr int FRAMES = 512;

  int16_t buffer[FRAMES] = {0};

  const int totalFrames =
    SAMPLE_RATE * durationMs / 1000;

  int framesPlayed = 0;

  while (framesPlayed < totalFrames) {
    const int framesThisTime =
      min(
        FRAMES,
        totalFrames - framesPlayed
      );

    writeMonoToSpeaker(buffer, framesThisTime);

    framesPlayed += framesThisTime;
  }
}

void stopAllWavPlayback() {
  wavStreamStop();
}

bool tryStartButtonEventSound(const char* sound) {
  const ButtonSfxClip sfx = parseButtonSfx(sound);
  const bool animOwnsActive =
    wavStreamIsActive() && animationDrivesWavStream(getAnimation());
  if (!shouldStartButtonSfx(sfx, apiBusyHeld(), animOwnsActive)) {
    return false;
  }

  const WavClip clip = sfx == ButtonSfxClip::Bell ? WavClip::Bell : WavClip::Click;
  return wavStreamStart(clip);
}

void stopBellPlayback() {
  wavStreamStop();
}

void stopWelcomePlayback() {
  wavStreamStop();
}

void stopAttentionPlayback() {
  wavStreamStop();
}

void stopErrorPlayback() {
  wavStreamStop();
}

void stopAbortPlayback() {
  wavStreamStop();
}

void stopDeadPlayback() {
  wavStreamStop();
}

bool startBellPlayback() {
  return wavStreamStart(WavClip::Bell);
}

bool startWelcomePlayback() {
  return wavStreamStart(WavClip::Welcome);
}

bool startAttentionPlayback() {
  return wavStreamStart(WavClip::Attention);
}

bool startErrorPlayback() {
  return wavStreamStart(WavClip::Error);
}

bool startAbortPlayback() {
  return wavStreamStart(WavClip::Abort);
}

bool startDeadPlayback() {
  return wavStreamStart(WavClip::Dead);
}

bool updateBellPlayback() {
  return wavStreamUpdate();
}

bool updateWelcomePlayback() {
  return wavStreamUpdate();
}

bool updateAttentionPlayback() {
  return wavStreamUpdate();
}

bool updateErrorPlayback() {
  return wavStreamUpdate();
}

bool updateAbortPlayback() {
  return wavStreamUpdate();
}

bool updateDeadPlayback() {
  return wavStreamUpdate();
}

bool playBell() {
  return playWavBlocking(WavClip::Bell, "Playing...");
}

bool playWelcome() {
  return playWavBlocking(WavClip::Welcome, "Playing...");
}

bool playAttention() {
  return playWavBlocking(WavClip::Attention, "Playing...");
}

bool playError() {
  return playWavBlocking(WavClip::Error, "Playing...");
}

bool playAbort() {
  return playWavBlocking(WavClip::Abort, "Playing...");
}

bool playDead() {
  return playWavBlocking(WavClip::Dead, "Playing...");
}

void runSoundTest() {
  stopAllWavPlayback();
  serialLogPrintln();
  serialLogPrintln("==========================");
  serialLogPrintln("SOUND TEST");
  serialLogPrintln("==========================");

  showOledText(
    "SOUND TEST",
    "500 Hz"
  );

  playTone(500, 120);
  playSilence(50);

  showOledText(
    "SOUND TEST",
    "700 Hz"
  );

  playTone(700, 120);
  playSilence(50);

  showOledText(
    "SOUND TEST",
    "1000 Hz"
  );

  playTone(1000, 220);
  playSilence(100);

  showOledText(
    "SOUND TEST",
    "OK"
  );

  serialLogPrintln("Sound OK");

  delay(500);
}
