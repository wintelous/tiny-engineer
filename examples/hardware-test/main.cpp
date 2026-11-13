#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <TinyEngineerExpressions.h>

#include "pins.h"

namespace expressions = tiny_engineer::expressions;

static_assert(I2C_SDA == 0 && I2C_SCL == 1 && PCA9685_OE_PIN == 5);
static_assert(RGB_RED_PIN == 6 && RGB_GREEN_PIN == 7 && RGB_BLUE_PIN == 10);
static_assert(OLED_WIDTH == expressions::kWidth && OLED_HEIGHT == expressions::kHeight,
              "Expression frame dimensions must match the OLED buffer");

// Keep OLED frame transfers at scan speed instead of the library's 400 kHz default.
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1, 100000, 100000);
uint8_t frame[expressions::kFrameBytes];
bool oledReady = false;
uint32_t started = 0;
uint32_t lastFrame = 0;
uint8_t lastColor = 255;
uint8_t lastExpression = 255;

int readPcaRegister(uint8_t reg) {
  // Auto-increment is disabled after PCA9685 power-on; read each register separately.
  Wire.beginTransmission(PCA9685_ADDRESS);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0 ||
      Wire.requestFrom(PCA9685_ADDRESS, uint8_t{1}) != 1) return -1;
  return Wire.read();
}

void setup() {
  pinMode(PCA9685_OE_PIN, OUTPUT);
  digitalWrite(PCA9685_OE_PIN, HIGH);
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);
  delay(1000);
  Serial.println("BENCH: RGB 6/7/10; I2C SDA=0 SCL=1; servo OE=HIGH");

  bool found[128] = {};
  if (Wire.begin(I2C_SDA, I2C_SCL)) {
    Wire.setTimeOut(100);
    for (uint8_t address = 8; address < 120; address++) {
      Wire.beginTransmission(address);
      if (Wire.endTransmission() == 0) {
        found[address] = true;
        Serial.printf("I2C ACK: 0x%02X\n", address);
      }
    }
  } else {
    Serial.println("I2C FAIL: bus initialization");
  }

  if (found[PCA9685_ADDRESS]) {
    const int mode1 = readPcaRegister(0x00);
    const int mode2 = readPcaRegister(0x01);
    if (mode1 >= 0 && mode2 >= 0) {
      Serial.printf("PCA PASS: address=0x%02X MODE1=0x%02X MODE2=0x%02X; outputs disabled\n",
                    PCA9685_ADDRESS, mode1, mode2);
    } else {
      Serial.println("PCA FAIL: address acknowledged but register read failed");
    }
  } else {
    Serial.println("PCA FAIL: no device at 0x40; check VCC=3V3, GND, SDA and SCL");
  }

  const uint8_t oledAddress = found[OLED_ADDRESS] ? OLED_ADDRESS : 0x3D;
  if (found[oledAddress]) {
    oledReady = display.begin(SSD1306_SWITCHCAPVCC, oledAddress, true, false);
    if (oledReady) {
      display.setRotation(2);
      Serial.printf("OLED PASS: address=0x%02X size=%dx%d rotation=180\n",
                    oledAddress, OLED_WIDTH, OLED_HEIGHT);
      Wire.beginTransmission(oledAddress);
      Wire.write(uint8_t{0x00});
      Wire.write(SSD1306_DISPLAYALLON);
      const uint8_t status = Wire.endTransmission();
      Serial.printf("OLED: full-panel flash, I2C status=%u\n", status);
      delay(2000);
      display.ssd1306_command(SSD1306_DISPLAYALLON_RESUME);
      display.clearDisplay();
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(1);
      display.setCursor(0, 0);
      display.println("OLED TEST");
      display.println("SDA=0  SCL=1");
      display.println("I2C=100 kHz");
      display.display();
      Serial.println("OLED: text screen for three seconds");
      delay(3000);
    } else {
      Serial.println("OLED FAIL: initialization");
    }
  } else {
    Serial.println("OLED FAIL: no device at 0x3C or 0x3D");
  }
  Serial.println("RGB: repeating RED GREEN BLUE WHITE OFF; two seconds each");
  started = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t elapsed = now - started;
  const char* names[] = {"RED", "GREEN", "BLUE", "WHITE", "OFF"};
  const uint8_t levels[][3] = {
    {255, 0, 0}, {0, 255, 0}, {0, 0, 255}, {255, 255, 255}, {0, 0, 0}
  };
  static_assert(sizeof(names) / sizeof(names[0]) == sizeof(levels) / sizeof(levels[0]));
  const uint8_t color = (elapsed / 2000) % 5;
  if (color != lastColor) {
    analogWrite(RGB_RED_PIN, levels[color][0]);
    analogWrite(RGB_GREEN_PIN, levels[color][1]);
    analogWrite(RGB_BLUE_PIN, levels[color][2]);
    Serial.printf("RGB: %s\n", names[color]);
    lastColor = color;
  }

  if (!oledReady || now - lastFrame < expressions::kFrameDurationMs) return;
  lastFrame = now;
  const uint8_t index = (elapsed / expressions::kLoopDurationMs) % expressions::kExpressionCount;
  const auto expression = static_cast<expressions::Expression>(index);
  if (index != lastExpression) {
    Serial.printf("OLED: %s\n", expressions::name(expression));
    lastExpression = index;
  }
  if (expressions::render(expression, elapsed % expressions::kLoopDurationMs,
                          frame, sizeof(frame))) {
    display.clearDisplay();
    display.drawBitmap(0, 0, frame, OLED_WIDTH, OLED_HEIGHT, SSD1306_WHITE);
    display.display();
  }
}
