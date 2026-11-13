#pragma once

#include <stdint.h>

enum class WavClip : uint8_t {
  Bell,
  Welcome,
  Attention,
  Error,
  Abort,
  Dead,
  Click,
};

constexpr uint8_t kWavClipCount = 7;

const char* wavClipPath(WavClip clip);
const char* wavClipOledTitle(WavClip clip);

bool wavStreamStart(WavClip clip);
// Playback runs on the audio task; this refreshes volume and reports activity.
bool wavStreamUpdate();
void wavStreamStop();
bool wavStreamIsPlaying(WavClip clip);
bool wavStreamIsActive();
