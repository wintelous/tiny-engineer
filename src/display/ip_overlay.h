#pragma once

#include <cstdint>

// Show the robot's WiFi IP on the OLED for a few seconds without blocking the
// loop, then hand the screen back to the eyes (or back to sleep). Calling it
// again while the IP is up restarts the timer.
void showIpOverlay(uint32_t now);
void updateIpOverlay(uint32_t now);
