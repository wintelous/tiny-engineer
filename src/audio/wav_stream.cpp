#include "audio/wav_stream.h"

#include <Arduino.h>
#include <ESP_I2S.h>
#include <FS.h>
#include <LittleFS.h>
#include <atomic>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>

#include "audio/audio.h"
#include "audio/wav_header.h"
#include "pins.h"
#include "settings/settings.h"
#include "serial_log.h"

namespace {

constexpr int kAudioFrames = 512;

struct WavClipDef {
  const char* path;
  const char* label;
  const char* oledTitle;
};

constexpr WavClipDef kClips[kWavClipCount] = {
  {"/bell.wav", "Bell", "BELL"},
  {"/welcome.wav", "Welcome", "WELCOME"},
  {"/attention.wav", "Attention", "ATTENTION"},
  {"/error.wav", "Error", "ERROR"},
  {"/abort.wav", "Abort", "ABORT"},
  {"/dead.wav", "Dead", "DEAD"},
  {"/click.wav", "Click", "CLICK"},
};

File g_file;
std::atomic<bool> g_playing{false};
std::atomic<bool> g_finished{false};
std::atomic<uint8_t> g_volume{100};
WavClip g_active = WavClip::Bell;
SemaphoreHandle_t g_fileMutex = nullptr;
TaskHandle_t g_audioTask = nullptr;

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

struct WavFileReader {
  File& file;

  bool read(uint8_t* dest, size_t len) {
    return file.read(dest, len) == len;
  }

  bool skip(uint32_t len) {
    return file.seek(file.position() + len);
  }
};

bool pumpWavChunk(File& file) {
  int16_t samples[kAudioFrames];

  const size_t bytesRead =
    file.read(
      reinterpret_cast<uint8_t*>(samples),
      sizeof(samples)
    );

  if (bytesRead < 2) {
    return false;
  }

  writeMonoToSpeaker(samples, bytesRead / 2, g_volume.load());

  return file.available() > 0;
}

const WavClipDef& clipDef(WavClip clip) {
  return kClips[static_cast<uint8_t>(clip)];
}

void feedAudio(void*) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    while (g_playing) {
      xSemaphoreTake(g_fileMutex, portMAX_DELAY);
      if (g_playing && !pumpWavChunk(g_file)) {
        g_file.close();
        g_finished = true;
        g_playing = false;
      }
      xSemaphoreGive(g_fileMutex);
      vTaskDelay(1);
    }
  }
}

bool ensureAudioTask() {
  if (g_audioTask) return true;
  g_fileMutex = xSemaphoreCreateMutex();
  if (!g_fileMutex) return false;
  // Feed DMA independently of the slow OLED transfers in the animation loop.
  if (xTaskCreate(feedAudio, "wav_audio", 6144, nullptr, 2, &g_audioTask) != pdPASS) {
    vSemaphoreDelete(g_fileMutex);
    g_fileMutex = nullptr;
    return false;
  }
  return true;
}

}  // namespace

const char* wavClipPath(WavClip clip) {
  return clipDef(clip).path;
}

const char* wavClipOledTitle(WavClip clip) {
  return clipDef(clip).oledTitle;
}

bool wavStreamStart(WavClip clip) {
  wavStreamStop();

  const WavClipDef& def = clipDef(clip);

  if (!initAudioStorage()) {
    serialLogPrint(def.label);
    serialLogPrintln(" failed: filesystem");
    return false;
  }

  if (!ensureAudioTask()) {
    serialLogPrintln("WAV failed: audio task unavailable");
    return false;
  }

  xSemaphoreTake(g_fileMutex, portMAX_DELAY);
  g_file = LittleFS.open(def.path, "r");

  if (!g_file) {
    xSemaphoreGive(g_fileMutex);
    logAudioStorageContents();
    serialLogPrint(def.label);
    serialLogPrint(" failed: ");
    serialLogPrint(def.path);
    serialLogPrintln(" missing");
    return false;
  }

  WavFileReader reader{g_file};
  const WavHeaderResult header = readWavHeader(reader, SAMPLE_RATE);

  if (header != WavHeaderResult::Ok) {
    g_file.close();
    xSemaphoreGive(g_fileMutex);
    serialLogPrint(def.label);
    serialLogPrint(" failed: invalid WAV (");
    serialLogPrint(wavHeaderResultText(header));
    serialLogPrintln(")");
    return false;
  }

  g_active = clip;
  g_finished = false;
  g_volume = settingsVolume();
  g_playing = true;
  xSemaphoreGive(g_fileMutex);
  serialLogPrint("Playing ");
  serialLogPrintln(def.path);
  xTaskNotifyGive(g_audioTask);
  return true;
}

bool wavStreamUpdate() {
  g_volume = settingsVolume();
  if (g_finished.exchange(false)) {
    serialLogPrint(clipDef(g_active).label);
    serialLogPrintln(" OK");
  }
  return g_playing;
}

void wavStreamStop() {
  if (!g_fileMutex) return;
  xSemaphoreTake(g_fileMutex, portMAX_DELAY);
  g_playing = false;
  g_finished = false;
  if (g_file) {
    g_file.close();
  }
  xSemaphoreGive(g_fileMutex);
}

bool wavStreamIsPlaying(WavClip clip) {
  return g_playing && g_active == clip;
}

bool wavStreamIsActive() {
  return g_playing;
}
