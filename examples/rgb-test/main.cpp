#include <Arduino.h>

#include "pins.h"

static_assert(RGB_RED_PIN == 6 && RGB_GREEN_PIN == 7 && RGB_BLUE_PIN == 10);

void setup() {
  pinMode(PCA9685_OE_PIN, OUTPUT);
  digitalWrite(PCA9685_OE_PIN, HIGH);
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);
  delay(1000);
}

void loop() {
  const char* names[] = {"RED", "GREEN", "BLUE", "WHITE", "OFF"};
  const uint8_t levels[][3] = {
    {255, 0, 0}, {0, 255, 0}, {0, 0, 255}, {255, 255, 255}, {0, 0, 0}
  };
  static_assert(sizeof(names) / sizeof(names[0]) == sizeof(levels) / sizeof(levels[0]));

  for (int i = 0; i < 5; i++) {
    Serial.println(names[i]);
    analogWrite(RGB_RED_PIN, levels[i][0]);
    analogWrite(RGB_GREEN_PIN, levels[i][1]);
    analogWrite(RGB_BLUE_PIN, levels[i][2]);
    delay(2000);
  }
}
