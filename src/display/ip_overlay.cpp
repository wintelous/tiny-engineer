#include "display/ip_overlay.h"

#include "display/eyes.h"
#include "display/oled.h"
#include "network/wifi_connect.h"
#include "sleep.h"

namespace {

constexpr uint32_t kIpOverlayMs = 4000;

bool g_active = false;
uint32_t g_startedMs = 0;

}  // namespace

void showIpOverlay(uint32_t now) {
  // Setup AP mode already cycles the AP address on the screen.
  if (!oledAvailable || wifiProvisioningMode()) {
    return;
  }

  holdEyes(true);
  wakeOled();
  showBootIp(wifiConnected() ? wifiIpText() : "");
  g_active = true;
  g_startedMs = now;
}

void updateIpOverlay(uint32_t now) {
  if (!g_active || now - g_startedMs < kIpOverlayMs) {
    return;
  }

  g_active = false;
  holdEyes(false);

  if (isSleeping()) {
    sleepOled();
  } else if (!eyesActive()) {
    blankOled();
  }
}
