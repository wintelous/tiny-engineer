#pragma once

#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_SSD1306.h>
#include <esp_timer.h>

#include "wifi_credentials.h"

WebServer server(80);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1, 100000, 100000);
esp_timer_handle_t releaseTimer = nullptr;
bool oledReady = false;
String shownAddress;

void printWiFiStatus() {
  Serial.printf("WIFI state: %d; WIFI IP: %s\n", WiFi.status(), WiFi.localIP().toString().c_str());
}

bool startReleaseTimer() {
  return releaseTimer && esp_timer_start_once(releaseTimer, 2000000) == ESP_OK;
}

void cancelReleaseTimer() {
  if (releaseTimer) esp_timer_stop(releaseTimer);
}

bool authorized() {
  if (server.header("Authorization") == String("Bearer ") + SERVO_API_TOKEN) return true;
  server.send(401, "text/plain", "Control key required");
  return false;
}

void sendServoStatus() {
  const bool active = outputsEnabled && digitalRead(PCA9685_OE_PIN) == LOW;
  server.send(200, "application/json", String("{\"ready\":") +
              (controllerReady ? "true" : "false") + ",\"outputs\":" +
              (active ? "true" : "false") + "}");
}

void handleHttpCommand() {
  if (!authorized()) return;
  const String text = server.arg("plain");
  if (server.header("Content-Type") != "text/plain" || server.args() != 1 ||
      server.clientContentLength() != static_cast<int>(text.length())) {
    server.send(400, "text/plain", "Send only a text/plain command body");
    return;
  }
  const bool off = text == "OFF";
  if (!off && !validMoveCommand(text.c_str(), text.length())) {
    server.send(400, "text/plain", "Body: C0..C4, -0..-4, +0..+4 or OFF");
    return;
  }
  if (!off && outputsEnabled) {
    server.send(409, "text/plain", "Wait for release or send OFF");
    return;
  }
  if (!off && !controllerReady) {
    server.send(503, "text/plain", "Controller unavailable; outputs disabled");
    return;
  }
  handleCommand(text.c_str(), text.length());
  if (!off && !outputsEnabled) {
    server.send(503, "text/plain", "Move failed; outputs disabled");
    return;
  }
  sendServoStatus();
}

void setupWiFiControl() {
  esp_timer_create_args_t args = {};
  // Timer-task GPIO cutoff remains effective while the HTTP server is blocked.
  args.callback = [](void*) { digitalWrite(PCA9685_OE_PIN, HIGH); };
  args.name = "servo_release";
  if (esp_timer_create(&args, &releaseTimer) != ESP_OK) {
    controllerReady = false;
    Serial.println("FAIL: release timer; outputs disabled");
  }
  oledReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS, true, false);
  if (oledReady) {
    display.setRotation(2);
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
  }
  const char* headers[] = {"Authorization", "Content-Type"};
  server.collectHeaders(headers, 2);
  server.on("/", HTTP_GET, [] {
    server.send(200, "text/plain", "Servo bench: GET /status; POST /command with text/plain body.\n"
                "C0..C4 = neutral; -0..-4 / +0..+4 = small moves; OFF = release.\n"
                "API requires Authorization: Bearer <control key>.\n");
  });
  server.on("/status", HTTP_GET, [] { if (authorized()) sendServoStatus(); });
  server.on("/command", HTTP_POST, handleHttpCommand);
  server.onNotFound([] { server.send(404, "text/plain", "Not found"); });
  WiFi.persistent(false);
  WiFi.onEvent([](arduino_event_id_t, arduino_event_info_t info) {
    Serial.printf("WIFI disconnected: reason=%u\n", info.wifi_sta_disconnected.reason);
  }, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  // This board times out authenticating at default RF power; verify at 8.5 dBm.
  Serial.printf("WIFI TX 8.5 dBm configured: %d\n", WiFi.setTxPower(WIFI_POWER_8_5dBm));
  Serial.printf("WIFI sleep disabled: %d\n", WiFi.setSleep(false));
  server.begin();
  Serial.println("WIFI: connecting; servo outputs OFF");
}

void loopWiFiControl() {
  const bool connected = WiFi.status() == WL_CONNECTED;
  if (!connected && outputsEnabled) stopOutputs();
  const String address = connected ? WiFi.localIP().toString() : String("Connecting...");
  if (address != shownAddress) {
    shownAddress = address;
    Serial.printf("WIFI IP: %s\n", address.c_str());
    if (oledReady) {
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("Hugge WiFi");
      display.println(address);
      display.println(controllerReady ? "Servo test ready" : "Controller FAIL");
      display.display();
    }
  }
  if (connected) server.handleClient();
}
