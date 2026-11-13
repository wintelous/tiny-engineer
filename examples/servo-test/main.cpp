#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <cstring>
#ifdef SERVO_WIFI_TEST
#include <Network.h>
#include <WiFi.h>
#include <WebServer.h>
#endif

#include "pins.h"

Adafruit_PWMServoDriver pwm(PCA9685_ADDRESS);
bool controllerReady = false;
bool outputsEnabled = false;
uint32_t moveStarted = 0;
char command[8];
uint8_t commandLength = 0;
bool commandOverflow = false;

#ifdef SERVO_WIFI_TEST
bool startReleaseTimer();
void cancelReleaseTimer();
void setupWiFiControl();
void loopWiFiControl();
void printWiFiStatus();
#endif

bool validMoveCommand(const char* text, size_t length) {
  return length == 2 && (text[0] == 'C' || text[0] == '-' || text[0] == '+') &&
         text[1] >= '0' && text[1] <= '4';
}

void stopOutputs() {
  digitalWrite(PCA9685_OE_PIN, HIGH);
#ifdef SERVO_WIFI_TEST
  cancelReleaseTimer();
#endif
  outputsEnabled = false;
  if (controllerReady) {
    for (uint8_t channel = 0; channel < 16; channel++) {
      if (pwm.setPWM(channel, 0, 4096) != 0) controllerReady = false;
    }
  }
}

void handleCommand(const char* text, uint8_t length) {
  if (length == 3 && memcmp(text, "OFF", 3) == 0) {
    stopOutputs();
    Serial.println("OFF: OE HIGH");
    return;
  }
  if (length == 6 && memcmp(text, "STATUS", 6) == 0) {
    Serial.printf("STATUS: controller=%s outputs=%s\n",
                  controllerReady ? "READY" : "FAIL", outputsEnabled ? "ON" : "OFF");
#ifdef SERVO_WIFI_TEST
    printWiFiStatus();
#endif
    return;
  }
  if (!validMoveCommand(text, length)) {
    Serial.println("ERROR: use C0..C4, -0..-4, +0..+4, OFF or STATUS");
    return;
  }

  stopOutputs();
  if (!controllerReady) {
    Serial.println("FAIL: controller unavailable; outputs disabled");
    return;
  }
  const uint8_t channel = text[1] - '0';
  const uint16_t pulseUs = text[0] == '-' ? 1450 : text[0] == '+' ? 1550 : 1500;
  const uint16_t count = (static_cast<uint32_t>(pulseUs) * 4096 + 10000) / 20000;
  if (pwm.setPWM(channel, 0, count) != 0) {
    controllerReady = false;
    Serial.println("FAIL: PWM write; OE HIGH");
    return;
  }
  moveStarted = millis();
#ifdef SERVO_WIFI_TEST
  if (!startReleaseTimer()) {
    controllerReady = false;
    Serial.println("FAIL: release timer; OE HIGH");
    return;
  }
#endif
  digitalWrite(PCA9685_OE_PIN, LOW);
  outputsEnabled = true;
  Serial.printf("PULSE: channel=%u nominal_us=%u counts=%u; releases in 2000 ms\n",
                channel, pulseUs, count);
}

#ifdef SERVO_WIFI_TEST
#include "wifi_control.h"
#endif

void setupServoController() {
  pinMode(PCA9685_OE_PIN, OUTPUT);
  digitalWrite(PCA9685_OE_PIN, HIGH);
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);
  delay(1000);
  if (!Wire.begin(I2C_SDA, I2C_SCL, 100000)) {
    Serial.println("FAIL: I2C; OE HIGH");
    return;
  }
  Wire.setTimeOut(100);
  controllerReady = pwm.begin();
  if (!controllerReady) {
    Serial.println("FAIL: PCA9685; OE HIGH");
    return;
  }
  pwm.setPWMFreq(50);
  delay(100);
  stopOutputs();
  Serial.println(controllerReady ? "SERVO READY: 50 Hz; all outputs OFF; commands required" :
                                   "FAIL: clearing PWM outputs; OE HIGH");
}

void setup() {
  setupServoController();
#ifdef SERVO_WIFI_TEST
  setupWiFiControl();
#endif
}

void loop() {
  if (outputsEnabled && static_cast<uint32_t>(millis() - moveStarted) >= 2000) {
    stopOutputs();
    Serial.println("AUTO OFF: OE HIGH");
  }
  for (uint8_t n = 0; n < 32 && Serial.available(); n++) {
    const char ch = Serial.read();
    if (ch == '\n') {
      if (!commandOverflow && commandLength > 0) handleCommand(command, commandLength);
      commandLength = 0;
      commandOverflow = false;
    } else if (ch != '\r') {
      if (commandLength < sizeof(command)) command[commandLength++] = ch;
      else commandOverflow = true;
    }
  }
#ifdef SERVO_WIFI_TEST
  loopWiFiControl();
#endif
}
