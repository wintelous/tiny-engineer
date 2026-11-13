#pragma once

#include <cstdint>

// =====================================================
// PINOUT
// =====================================================

// I2C -> PCA9685 + OLED
constexpr int I2C_SDA = 0;   // GP0
constexpr int I2C_SCL = 1;   // GP1

// I2S -> MAX98357A
constexpr int I2S_BCLK = 2;  // GP2
constexpr int I2S_LRC  = 3;  // GP3
constexpr int I2S_DIN  = 4;  // GP4

// Default Extension-port GPIO for the push-button extension (settings `push_button_pin`).
constexpr int PUSH_BUTTON_PIN_DEFAULT = 20;  // GP20

#if defined(TE_BOARD_SUPERMINI)
// ESP32-C3 SuperMini build (env:supermini): no onboard WS2812, so an external
// common-cathode RGB LED, each anode through its own 330-ohm resistor.
constexpr int RGB_RED_PIN = 6;    // GP6
constexpr int RGB_GREEN_PIN = 7;  // GP7
constexpr int RGB_BLUE_PIN = 10;  // GP10
#else
// Built-in WS2812 RGB
constexpr int RGB_LED_PIN = 10;
#endif

// PCA9685 output enable (active LOW). GP5 → OE; default on.
// Set PCA9685_OE_WIRED false only if OE is hard-tied off-chip (e.g. to GND).
constexpr bool PCA9685_OE_WIRED = true;
constexpr int PCA9685_OE_PIN = 5;

// =====================================================
// AUDIO
// =====================================================

// assets/ ships 44100 Hz WAVs; scripts/audio_pack.py halves them while packing LittleFS.
constexpr int SAMPLE_RATE = 22050;

#if defined(TE_BOARD_SUPERMINI)
// 22.05 kHz is not among the MAX98357A's supported clocks; the SuperMini build
// runs I2S at 44.1 kHz and sends each PCM frame twice.
constexpr int I2S_FRAME_REPEAT = 2;
// Long jumper wires to the OLED: keep its I2C at 100 kHz, also during frames.
constexpr uint32_t OLED_I2C_CLOCK_HZ = 100000;
#else
constexpr int I2S_FRAME_REPEAT = 1;
#endif
constexpr int I2S_SAMPLE_RATE = SAMPLE_RATE * I2S_FRAME_REPEAT;

// =====================================================
// PCA9685 / SERVOS
// =====================================================

constexpr uint8_t PCA9685_ADDRESS = 0x40;

constexpr int SERVO_STEP_MS = 10;

// Boot centering / sleep-pose rate (deg/s)
constexpr float SERVO_BOOT_SPEED_DEG_S = 35.0f;

// Servo pulse range
constexpr int SERVO_MIN_US = 800;
constexpr int SERVO_MAX_US = 2200;

// =====================================================
// OLED
// =====================================================

constexpr int OLED_WIDTH  = 128;
constexpr int OLED_HEIGHT = 32;
constexpr uint8_t OLED_ADDRESS = 0x3C;
