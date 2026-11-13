#include "robot_tick.h"

#include <Arduino.h>

#include "animation.h"
#include "audio/wav_stream.h"
#include "display/ip_overlay.h"
#include "display/oled.h"
#include "hardware/rgb.h"
#include "hardware/servo_wrapper.h"
#include "network/wifi_connect.h"
#include "sleep.h"

void tickRobot() {
  const uint32_t now = millis();
  pollWifi();
  updateProvisioningOled(now);
  updateIpOverlay(now);
  updateAnimation();
  // Refresh volume and completion state for orphan SFX; the audio task feeds DMA.
  if (wavStreamIsActive() && !animationDrivesWavStream(getAnimation())) {
    wavStreamUpdate();
  }
  // Read again: an animation applied this tick stamps its idle time after `now`.
  updateSleep(millis());
  updateRgb(now);
  pollServoPoseSave();
}
