# ESP32-C3 SuperMini build

A variant for an **ESP32-C3 SuperMini** on discrete breakouts (PCA9685, MAX98357A, SSD1306 OLED) instead of the Waveshare ESP32-C3-Zero. The desk parts that hold the SuperMini, a USB-C power breakout, a 20 mm speaker and a 5 mm lamp LED are in [`mods/esp32-c3-supermini`](../../mods/esp32-c3-supermini/README.md).

The stock builds are unchanged. Everything below is behind one build flag, `TE_BOARD_SUPERMINI`, set by the `supermini` PlatformIO environment.

## Build and flash

```bash
pio run -e supermini
pio test -e native
pio test -e native-supermini
```

`native-supermini` runs the settings checks with this build's pin rules. To flash, use the same targets as the stock build with `-e supermini` (`-t upload`, `-t uploadfs`).

Flash over the SuperMini's own USB-C with the servo supply and the external 5 V disconnected: the external 5 V feeds the SuperMini's 5V pin, and two USB supplies must never be connected at once. The SuperMini's USB data lines (GPIO18/19) are not on its headers, so its own port is the programming port; the USB-C power breakout only brings in 5 V.

## Wiring

| GPIO | Connection |
| --- | --- |
| 0 | OLED SDA and PCA9685 SDA |
| 1 | OLED SCL and PCA9685 SCL |
| 2 | MAX98357A BCLK |
| 3 | MAX98357A LRC |
| 4 | MAX98357A DIN |
| 5 | PCA9685 OE |
| 6 | 330 Ω → RGB red anode |
| 7 | 330 Ω → RGB green anode |
| 10 | 330 Ω → RGB blue anode |
| 9 | Onboard BOOT button; can be the push button (`push_button_pin: 9`) |

The RGB LED is common-cathode: cathode to GND, each anode through its own resistor. Power: external 5 V to the SuperMini's 5V pin, PCA9685 V+ and the amplifier's VIN; SuperMini 3V3 to the OLED VCC and the PCA9685 VCC; all grounds together. Board-by-board pin tables, including the USB-C power breakout: [mod README](../../mods/esp32-c3-supermini/README.md#wiring).

## What the flag changes

| Area | Stock | SuperMini build | Why |
| --- | --- | --- | --- |
| Status LED | Onboard WS2812 on GPIO10 | Common-cathode LED on GPIO6/7/10, 8-bit PWM | The SuperMini has no WS2812. `rgb_order` names the color on GPIO6, 7 and 10; the setup wizard's LED step still finds it |
| Push button pins | 6, 7, 9, 20, 21 | 9, 20, 21 | GPIO6/7 drive the LED |
| I2S clock | 22.05 kHz | 44.1 kHz, each 22.05 kHz frame sent twice (`I2S_FRAME_REPEAT`) | 22.05 kHz is not among the MAX98357A's supported clocks (datasheet). WAVs, streaming and motion timing stay at 22.05 kHz |
| OLED I2C | 400 kHz during frames | 100 kHz throughout (`OLED_I2C_CLOCK_HZ`); the library does not restart Wire | The OLED stayed blank at 400 kHz over jumper wires |
| Wi-Fi TX power | Default | 8.5 dBm | The SuperMini's antenna is unreliable at full power |
| Flash | QIO 80 MHz | DIO 40 MHz | Conservative timing for the SuperMini's flash chip |
| Defaults | volume 70, `rgb_order` GRB, OLED not rotated | volume 100, `rgb_order` RGB, OLED rotated 180° | This build's amp, LED wiring and OLED mounting. Saved settings still win |

The web UI is built with `VITE_TE_BOARD=supermini` (PlatformIO option `custom_ui_board`), so the Extensions page offers only pins 9, 20 and 21 and the LED setup step names GPIO6, 7 and 10.

## First boot

With only the SuperMini connected, boot stops at `PCA9685 not found` (one red blink once the LED is fitted). Connect the logic modules with the power off before expecting the setup access point, and keep the servo supply off, horns and linkages free, until the servos are centred and calibrated.
