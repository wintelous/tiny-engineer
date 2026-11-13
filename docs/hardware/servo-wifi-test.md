# SuperMini Wi-Fi servo bench firmware

This optional diagnostic extends the tested serial servo firmware. It does not
run the normal robot application, animate faces, play sounds, or change saved
calibration. Build with `pio run -e supermini-servo-wifi-test`. The SSD1306 128x32 display
shows the connected IP address at 180-degree rotation, using GPIO0/1 at 100 kHz.
The ESP32-C3 uses 2.4 GHz Wi-Fi. Connection retries automatically; outputs start
disabled and remain disabled while waiting for Wi-Fi.

Copy `examples/servo-test/wifi_credentials.example.h` to `wifi_credentials.h`
in the same directory and fill in SSID, password and a random control key. This
local header is ignored by Git. Credentials are compiled into the firmware;
keep the resulting binary private. Do not put credentials or the control key in
serial logs, screenshots, shared build artifacts, or project memory.

## Bench API

These routes exist only in `supermini-servo-wifi-test`, separately from the normal robot
API. Requests to `/status` and `/command` need the header
`Authorization: Bearer <control key>`.

| Method/path | Behavior |
| --- | --- |
| `GET /` | Public usage text; no movement or credentials |
| `GET /status` | JSON `ready` and `outputs` booleans |
| `POST /command` | Exact `text/plain` command body, no query parameters |

Commands are `C0`..`C4` (nominal 1500 us), `-0`..`-4` (1450 us),
`+0`..`+4` (1550 us), or `OFF` (disable). No whitespace or newline in HTTP bodies.
Only one channel runs at a time. New moves while active return 409; `OFF` is
accepted immediately. Invalid commands return 400, missing/wrong keys 401,
and unavailable controller or timer failures 503. No CORS access is enabled.

All other PWM channels are full-off before any enable. A separate ESP timer
task sets OE HIGH after two seconds even if the HTTP parser stalls. The main
loop then clears PWM and software state. Detected Wi-Fi disconnection also
disables outputs. Timer creation/start failure prevents enabling. Pulse widths
are nominal; the PCA9685 oscillator has not been measured or calibrated.

## Physical setup and updates

Use the existing Super Mini wiring in [supermini.md](supermini.md). For initial
tests connect only one servo, with horn/linkage detached, and keep hands clear.
Switch external servo power OFF before changing servo connections or flashing.
When computer USB powers the ESP32, external 5 V supplies PCA V+ only; grounds
are common, PCA VCC stays 3V3, and external positive must not connect to ESP32
5V. Do not power servo motors through the ESP32 regulator.

Flash only `.pio/build/supermini-servo-wifi-test/firmware.bin` at 0x10000 on the previously
prepared Super Mini. It uses the same partition table, leaves NVS/LittleFS
untouched and starts without movement. Check OLED/serial IP, authenticated
status and output shutdown with external servo power OFF before testing motion.

Host checks: `python3 scripts/test_servo_test.py` and
`python3 scripts/test_servo_wifi.py`. Physical Wi-Fi connectivity, OLED visibility
and movement must also be verified on the actual board.
