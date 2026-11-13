"""Compile the actual Wi-Fi servo diagnostic with fake HTTP, GPIO and timer APIs."""

from pathlib import Path
import subprocess
import tempfile

from test_servo_test import ARDUINO, WIRE, PWM, ROOT

WIFI = r'''
#pragma once
constexpr int WIFI_STA=1, WL_CONNECTED=3, ARDUINO_EVENT_WIFI_STA_DISCONNECTED=5;
constexpr int WIFI_POWER_8_5dBm=34;
using arduino_event_id_t=int;
struct arduino_event_info_t { struct { unsigned reason; } wifi_sta_disconnected; };
struct IPMock { String toString() { return "192.0.2.10"; } };
struct WiFiMock {
  int state=WL_CONNECTED;
  void persistent(bool value) { assert(!value); }
  void mode(int value) { assert(value==WIFI_STA); }
  void setAutoReconnect(bool value) { assert(value); }
  void begin(const char*,const char*) {}
  bool setTxPower(int value) { assert(value==WIFI_POWER_8_5dBm); return true; }
  bool setSleep(bool value) { assert(!value); return true; }
  template<class F> void onEvent(F,int) {}
  int status() { return state; }
  IPMock localIP() { return {}; }
};
inline WiFiMock WiFi;
'''

HTTP = r'''
#pragma once
#include <functional>
#include <map>
constexpr int HTTP_GET=0,HTTP_POST=1;
struct WebServer {
  int code=0,count=1,contentLength=2;
  String auth="Bearer test-token",body="C0",type="text/plain",reply;
  std::map<String,std::function<void()>> routes;
  explicit WebServer(int port) { assert(port==80); }
  void collectHeaders(const char**,int count) { assert(count==2); }
  void on(const char* path,int method,std::function<void()> fn) {
    assert((String(path)=="/command")==bool(method==HTTP_POST)); routes[path]=fn;
  }
  void onNotFound(std::function<void()>) {}
  void begin() {}
  void handleClient() {}
  String header(const char* key) { return String(key)=="Authorization" ? auth : type; }
  String arg(const char* key) { assert(String(key)=="plain"); return body; }
  int args() { return count; }
  int clientContentLength() { return contentLength; }
  void send(int status,const char*,const String& text) { code=status; reply=text; }
};
'''

OLED = r'''
#pragma once
constexpr int SSD1306_SWITCHCAPVCC=2,SSD1306_WHITE=1;
struct Adafruit_SSD1306 {
  String text;
  Adafruit_SSD1306(int w,int h,WireMock*,int reset,int during,int after) {
    assert(w==128 && h==32 && reset==-1 && during==100000 && after==100000);
  }
  bool begin(int,int address,bool,bool resetBus) { assert(address==0x3C && !resetBus); return true; }
  void setRotation(int n) { assert(n==2); }
  void setTextColor(int) {}
  void setTextSize(int) {}
  void clearDisplay() { text.clear(); }
  void setCursor(int,int) {}
  void println(const String& value) { text+=value; }
  void display() {}
};
'''

TIMER = r'''
#pragma once
constexpr int ESP_OK=0;
struct esp_timer_create_args_t { void(*callback)(void*); void* arg; const char* name; };
struct TimerMock { void(*callback)(void*)=nullptr; bool active=false,failStart=false; };
using esp_timer_handle_t=TimerMock*;
inline TimerMock timer;
inline int esp_timer_create(esp_timer_create_args_t* args,esp_timer_handle_t* handle) {
  timer.callback=args->callback; *handle=&timer; return ESP_OK;
}
inline int esp_timer_start_once(esp_timer_handle_t handle,uint64_t us) {
  assert(handle==&timer && us==2000000 && !timer.active);
  if(timer.failStart) return 1;
  timer.active=true; return ESP_OK;
}
inline int esp_timer_stop(esp_timer_handle_t handle) { handle->active=false; return ESP_OK; }
'''

CHECK = r'''
#define SERVO_WIFI_TEST
#include "main.cpp"
void digitalWrite(int pin,int level) {
  assert(pin==5);
  if(level==LOW) {
    assert(timer.active);
    int active=0;
    for(int value:pwm.counts) if(value!=4096) { assert(value>=297 && value<=317); active++; }
    assert(active==1); enables++;
  }
  oe=level;
}
void request(const String& body) {
  server.body=body;server.contentLength=body.length();server.routes["/command"]();
}
int main() {
  setup(); assert(controllerReady && !outputsEnabled && oe==HIGH && enables==0);
  loop(); assert(display.text.find("192.0.2.10")!=String::npos);
  server.auth=""; request("C3"); assert(server.code==401 && enables==0);
  server.auth="Bearer test-token";
  for(const char* invalid:{"C5","C-1","C3junk","1500","","OFFx"}) {
    request(invalid); assert(server.code==400 && enables==0);
  }
  server.type="application/json"; request("C3"); assert(server.code==400 && enables==0);
  server.type="text/plain";server.count=2;request("C3");assert(server.code==400 && enables==0);
  server.count=1;request("C3");assert(server.code==200 && outputsEnabled && pwm.counts[3]==307);
  request("+3");assert(server.code==409 && enables==1);
  // Simulate a blocked HTTP loop: the independent timer must still disable GPIO.
  timer.active=false;timer.callback(nullptr);assert(oe==HIGH);
  server.routes["/status"]();assert(server.reply.find("\"outputs\":false")!=String::npos);
  now+=2000;loop();assert(!outputsEnabled);
  request("-4");assert(server.code==200 && pwm.counts[4]==297);
  request("OFF");assert(!outputsEnabled && oe==HIGH && !timer.active);
  request("+2");assert(server.code==200 && pwm.counts[2]==317);
  WiFi.state=0;loop();assert(!outputsEnabled && oe==HIGH && !timer.active);
  WiFi.state=WL_CONNECTED;timer.failStart=true;
  request("C1");assert(server.code==503 && !outputsEnabled && oe==HIGH && !controllerReady);
}
'''


def main():
    with tempfile.TemporaryDirectory(prefix="tiny-servo-wifi-check-") as tmp:
        directory = Path(tmp)
        sources = {"Arduino.h": ARDUINO + '\nusing String=std::string;\n'
                   'inline int digitalRead(int pin) { assert(pin==5); return oe; }\n',
                   "Wire.h": WIRE, "Adafruit_PWMServoDriver.h": PWM,
                   "Network.h": "", "WiFi.h": WIFI, "WebServer.h": HTTP,
                   "Adafruit_SSD1306.h": OLED, "esp_timer.h": TIMER,
                   "wifi_credentials.h": '#define WIFI_SSID "test"\n'
                   '#define WIFI_PASSWORD "test"\n#define SERVO_API_TOKEN "test-token"\n',
                   "check.cpp": CHECK}
        for name in ["main.cpp", "wifi_control.h"]:
            sources[name] = (ROOT / "examples/servo-test" / name).read_text()
        for name, source in sources.items():
            (directory / name).write_text(source)
        exe = directory / "check"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        f"-I{directory}", f"-I{ROOT / 'include'}",
                        str(directory / "check.cpp"), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print("PASS: Wi-Fi IP display, authorization, input validation, one channel, independent cutoff, disconnect and timer failure")


if __name__ == "__main__":
    main()
