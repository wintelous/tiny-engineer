# ESP32-C3 SuperMini

Optional mod for builds that use an **ESP32-C3 SuperMini** instead of the Waveshare ESP32-C3-Zero, with discrete breakout boards (the [modular path](../../docs/3d/assembly-modular.md)). Not for the main control board.

The SuperMini hangs under the desk top in the USB corner. Its USB-C comes out through the desk wall, its component side (USB-C, BOOT, RST) faces the desk top, and its header pins face the open cavity for jumper wires. A pin through the desk top reaches the BOOT button, and a 5 mm RGB LED under the lamp replaces the C3-Zero status LED.

Firmware: `pio run -e supermini`. What that build changes and how to flash it: [docs/hardware/supermini.md](../../docs/hardware/supermini.md).

Status: SG90 only. The SuperMini corner and the power breakout mount have been test-printed. The rest is checked in CAD only.

## Parts

| File | Replaces | Notes |
| --- | --- | --- |
| `Desk` | stock `Desk` | Print like the stock part (desk top on the bed). |
| `DeskSuperMiniFitTest` | — | Corner of the new `Desk` only: no slatted end wall, cut at 18.6 mm just above the clips, LED tube included. Print it first to check the fit. |
| `DeskUsbPowerFitTest` | — | The other end of the same wall, cut just above the USB-C power breakout. |
| `DeskSpeakerFitTest` | — | The speaker holder on a 28 mm square of desk top. |
| `DeskTop` | stock `DeskTop` | C3-Zero cut closed, 5.2 mm light hole over the LED, 3.2 mm hole for the BOOT pusher. |
| `DeskPad` | stock `DeskPad` | 3.2 mm hole for the BOOT pusher. |
| `LampBase` | stock `LampBase` | `LampButton` hole closed. |
| `BootPusher` | stock `LampButton` (not needed) | Print upright, collar on the bed. |
| `LampDiffuserClear` | stock `LampDiffuser` (optional) | Solid light pipe for clear resin (SLA/MSLA). Needs the mod `DeskTop`. |
| `LampDiffuserClearSnug` | stock `LampDiffuser` (optional) | Same, with 0.1 mm clearance in every part it goes into. |

To see the fit before printing, open [`3d_models/cad/DeskSuperMiniAssembly.step`](3d_models/cad/DeskSuperMiniAssembly.step) in FreeCAD or Fusion: the new `Desk` with the SuperMini, the USB-C power breakout and the speaker seated, plus the desk-top stack, the lamp with `LampDiffuserClear`, a 5 mm LED and the BOOT pusher, coloured. Board components other than the outline, USB-C, buttons and pins are approximate.

## What changed in `Desk`

- **USB-C opening** moved 1.15 mm towards the chair arm (same size and counterbore). The corner screw boss leaves only 18 mm between the walls, the exact board width, so the board sits off the stock opening's axis.
- **Corner screw boss** shaved 0.5 mm on the side facing the board, full height. The screw hole is untouched.
- **USB-C rest**: a pillar under the receptacle shell.
- **Stock plateau removed** (the main control board seat). The LampBase screw pilot through the desk top is kept, now in a boss with a 1.5 mm wall.
- **C3-Zero pin slots closed.** One 5.1 mm hole under the lamp instead, at x = 1.90, y = −55.95 (the centre of the `LampBase` opening). A tube on the cavity side makes it 7.5 mm deep: push a 5 mm LED in from below until its flange stops at the tube end; the dome then sits flush with the desk top.
- **Rest at the antenna end**: a wedge across the board width with a 45° flank, topped by two short fingers that touch the PCB clear of the antenna and the pin rows.
- **Two snap clips** beside the rest, 2.4 mm thick at the root tapering to 1.6 mm at the hook, with a 0.55 mm gap to the rest and to the back wall.
- **Back wall** between the clips, 4 mm thick and 0.15 mm behind the antenna edge of the PCB, joined to the rest and the screw boss. It takes the push of a USB-C plug so the clips do not.
- **BOOT pusher guide**: a 3.0 mm bore through the desk top with a 1.5 mm wall tube that ends about 2 mm above the button.
- **USB-C power breakout** at the other end of the same wall, replacing the Adafruit 5993 mount: the vertical slot and four M2 holes are filled, and a horizontal opening (same width, height and counterbore as the SuperMini one, but 3.5 mm tall instead of 4 mm) runs through the thick wall. The breakout lies flat on two bosses and is held by two **M3×6** thread-forming screws driven in from inside the desk (2.5 mm pilots, 7 mm deep).
- **Speaker holder** for a round 20 mm speaker (2.4 mm rim, 3.25 mm at the bump on its back), lying flat under the desk top between the LED tube and the desk centre hole (centre x = 3.5, y = −26), membrane towards the cavity. Three pads hold it 8.85 mm off the desk top, which leaves air behind it. They touch only the outer edge of the rim (radius 8.4–9.6 mm), clear of the 10.9 mm magnet bump and the ring of vent holes, and widen below the bump. Turn the speaker so its solder tab sits between two pads; three curved snaps at 120°, 6.5 mm wide, hook 0.4 mm over its front rim. The snaps grow from the desk top with a 1 mm root fillet and flex over about 10 mm (2.0 mm thick at the root, 1.2 mm at the hook; about 1.7 % strain when they open).

## USB-C power breakout

Generic green 24-pin USB-C female breakout: PCB 20.5 × 10.2 mm, two 3 mm holes 15.6 mm apart and 2.6 mm from the connector edge, shell 10.8 mm long. The shell is assumed centred on the PCB thickness, like a board-edge straddle connector. If yours sits on top of the PCB instead, set `P_USB_ABOVE` in the script (shell centre above the PCB mid-plane) and re-run it; `P_PCB_T` (1.6 mm) and `P_USB_PAST_EDGE` (11.3 mm, shell front to PCB edge, set from the printed fit test) are next to it.

## Fit

1. Tilt the board and slide the USB-C into the wall opening from inside.
2. Press the antenna end towards the desk top until both clips snap over the PCB.
3. To remove it, push both clips towards the desk centre and lift the antenna end.

The clips allow a PCB thickness of about 0.8 to 1.2 mm. The script assumes 1.0 mm.

## BOOT pusher

`BootPusher` is a 2.5 mm pin, 19.9 mm long, with a 4 mm collar at the button end. It runs up through the 3.0 mm guide in `Desk` and the 3.2 mm holes in `DeskPad` and `DeskTop`. It rests on the BOOT button and stands 1.5 mm proud of the desk top. The collar sits under the guide tube, so the pin cannot leave through the top; it can rise 1.4 mm before the collar meets the tube.

1. With `DeskPad` and `DeskTop` screwed on and the board out, push the pin up through the guide from inside the desk, collar last.
2. Hold it there and clip in the board as described under Fit. The collar ends up on the BOOT button.

The length assumes the button top (actuator) is 1.9 mm above the PCB face. If your pin stands much more or less than 1.5 mm proud, set `BOOT_H` in `top_parts_supermini.py` to your measurement and re-run it, or sand the top.

To use the BOOT button as the robot's push button (Actions such as the bell on a click), turn on the push button on the Extensions page and pick GP9. Do not hold it while powering on or resetting: the SuperMini then starts in download mode.

Pressing the pin first takes up a few tenths of a millimetre of play in the board (the USB-C opening is 0.74 mm taller than the receptacle), then clicks the button.

## Desk top parts

- **`DeskTop`**: the C3-Zero cut is closed. A 5.2 mm hole over the LED lets the light through; `LampDiffuser` (6.7 mm) rests on its rim, at the height the C3-Zero used to hold it. A 3.2 mm hole with a 0.5 mm chamfer takes the pusher.
- **`DeskPad`**: a 3.2 mm hole for the pusher. The LED sits under the existing pad window.
- **`LampBase`**: the `LampButton` hole is filled to match the surface around it. Mount it with the same two M2 screws. Skip `LampButton`.

## Clear lamp diffuser

`LampDiffuserClear` replaces the thin FDM tube with a solid clear rod, the same 6.7 mm outside and 20 mm from the shoulder to the top, so `LampBase` and `LampCap` fit as before.

- **Light in:** a 4.8 mm spigot under the shoulder drops through the 5.2 mm light hole in the mod `DeskTop` and ends 0.4 mm above the LED dome, so most of the LED's light enters the rod. It does not fit the stock `DeskTop`.
- **Light up:** the rod carries the light by total internal reflection.
- **Glow:** six round helical grooves (0.45 mm deep, half a turn) run along the 12 mm you see between `LampBase` and `LampCap`. Each one breaks the reflection, so the light leaks out along glowing spiral lines, like a filament. Their rounded ends stay clear of both parts.

Printing:

1. Print it upright with the top (the end that goes into `LampCap`) flat on the build plate and no supports. The 0.3 mm chamfer there absorbs the flare of the first layers, and the spigot end, which takes the light in, is printed last and comes out clean.
2. Wash in IPA and cure briefly. Clear resin yellows when cured too long.
3. For the strongest spirals, make the smooth parts of the rod glassy so that only the grooves scatter light: wet-sand and polish, or dip the rod in the same clear resin (or brush on a clear coat), let it drip off and cure again. Leave it as printed for an even, frosted glow along the whole rod.
4. If it is tight in `LampBase` or `LampCap`, sand the rod lightly.

Two versions, the same apart from the fit:

| File | Rod | Spigot | Clearance per side |
| --- | --- | --- | --- |
| `LampDiffuserClear` | 6.7 mm | 4.8 mm | 0.15 mm in `LampBase` and `LampCap`, 0.2 mm in the `DeskTop` light hole |
| `LampDiffuserClearSnug` | 6.8 mm | 5.0 mm | 0.1 mm in all three |

Resin parts come out close to size, while the FDM-printed holes they go into often come out a little small. Print the snug one if the first one sits loose.

To change the grooves (count, depth, twist), the spigot length or the fits, edit the parameters at the top of [`lamp_diffuser_clear.py`](3d_models/cad/lamp_diffuser_clear.py) and re-run it.

## Wiring

This follows the [modular wiring](../../docs/hardware/wiring.md) for the SuperMini, the PCA9685 servo driver and the MAX98357A amplifier, with three changes: the SuperMini's own USB-C is the programming port, the green breakout only brings in power (its D+/D− stay unconnected), and a 5 mm common-cathode RGB LED under the lamp, on GPIO6/7/10, replaces the C3-Zero's onboard WS2812. The `supermini` build ([docs](../../docs/hardware/supermini.md)) drives that LED; the other pins are the stock ones in [`include/pins.h`](../../include/pins.h).

Two rails: **5 V** from the USB-C power breakout for the servos, the amp and the SuperMini, and **3.3 V** from the SuperMini for the logic of the PCA9685 and the OLED. Never connect them to each other. Every board shares one **GND**.

Each table lists every pin of one board and where it goes. A connection appears in the tables of both boards it joins.

### USB-C power breakout

| Pin | To | Notes |
| --- | --- | --- |
| **VBUS** | PCA9685 screw terminal **V+** | 5 V rail. Use thicker wire (22 AWG or so): it carries the servo current |
| **GND** | PCA9685 screw terminal **GND** | Common ground, same gauge |
| **CC1**, **CC2** | 5.1 kΩ each to GND | Only if the board has none (two resistors marked "512" near the connector). Without them a USB-C-to-C charger supplies nothing |
| **D+**, **D−**, others | — | Not used: the SuperMini's own USB-C is the programming port |

### ESP32-C3 SuperMini

| Pin | To | Notes |
| --- | --- | --- |
| **5V** | Schottky diode from the 5 V rail (PCA9685 terminal **V+**) | 1N5817 or SS14, band (cathode) on the SuperMini side |
| **GND** | PCA9685 header **GND** | Ground for the logic and signals |
| **3V3** | PCA9685 header **VCC**, OLED **VCC** | Logic supply only |
| **0** | PCA9685 **SDA**, OLED **SDA** | I2C data |
| **1** | PCA9685 **SCL**, OLED **SCL** | I2C clock |
| **2** | MAX98357A **BCLK** | I2S bit clock |
| **3** | MAX98357A **LRC** | I2S word select |
| **4** | MAX98357A **DIN** | I2S data |
| **5** | PCA9685 **OE** | Output enable, active low |
| **6** | LED red anode, through 330 Ω | Status LED |
| **7** | LED green anode, through 330 Ω | |
| **10** | LED blue anode, through 330 Ω | |
| **9** | — | Onboard BOOT button, pressed by `BootPusher`. Set `push_button_pin` to 9 to use it as the robot's push button |
| **20**, **21** | — | Free (push button pins) |
| **8** | — | Strapping pin and the blue onboard LED; do not pull low at reset |

Assume the SuperMini has no diode between its USB-C and its 5V pin. The diode on the 5V feed keeps a laptop on the SuperMini port from feeding the servo rail and stops the two supplies from fighting when both cables are in. Flashing works with or without the power cable.

### PCA9685 servo driver

Pin names as on the Adafruit 815; generic boards use the same names.

| Pin | To | Notes |
| --- | --- | --- |
| Screw terminal **V+** | Breakout **VBUS**; also MAX98357A **Vin** and the diode to SuperMini **5V** | 5 V rail |
| Screw terminal **GND** | Breakout **GND**; also MAX98357A **GND** | Common ground |
| Header **GND** | SuperMini **GND**, OLED **GND** | Same net as the terminal GND |
| Header **VCC** | SuperMini **3V3** | Chip logic, 3.3 V. Not the 5 V rail |
| Header **SDA** | SuperMini **0**, OLED **SDA** | |
| Header **SCL** | SuperMini **1**, OLED **SCL** | |
| Header **OE** | SuperMini **5** | |
| Header **V+** | — | Already joined to the terminal V+ on the board |
| Second header (right side) | — | For chaining another board, not used |
| Channel **0** | Head servo | Plug orientation on every channel: brown/black → GND, red → V+, orange → PWM |
| Channel **1** | Neck servo | |
| Channel **2** | Left hand servo | |
| Channel **3** | Right hand servo | |
| Channel **4** | Body servo | |
| Channels **5–15** | — | Free |

Leave the address jumpers open (address `0x40`). A 470–1000 µF capacitor across the terminal V+ and GND (the Adafruit board has a spot for it) helps when several servos start at once.

### MAX98357A amplifier

| Pin | To | Notes |
| --- | --- | --- |
| **Vin** | 5 V rail (PCA9685 terminal **V+**) | |
| **GND** | Common ground (PCA9685 terminal **GND**) | |
| **BCLK** | SuperMini **2** | |
| **LRC** | SuperMini **3** | |
| **DIN** | SuperMini **4** | |
| **GAIN** | — | Unconnected: 9 dB default |
| **SD** | — | Unconnected: on, left and right mixed |
| **+** | Speaker + | |
| **−** | Speaker − | Not ground. Never tie either speaker wire to GND |

### Other parts

| Part | Pin | To |
| --- | --- | --- |
| OLED | **VCC** | SuperMini **3V3** |
| OLED | **GND** | Common ground |
| OLED | **SDA** | SuperMini **0** |
| OLED | **SCL** | SuperMini **1** |
| LED | **Red** | SuperMini **6** through 330 Ω |
| LED | **Green** | SuperMini **7** through 330 Ω |
| LED | **Blue** | SuperMini **10** through 330 Ω |
| LED | **Cathode** (longest leg) | Common ground |

A 5 mm four-leg common-cathode RGB LED, one resistor per color. The `supermini` build drives the three pins with 8-bit PWM. If the colors come out swapped, the setup wizard's LED step finds the right order (`rgb_order`).

### Order and checks

Connect GND first, then the signals, then 3V3, then 5 V. Leave the servos unplugged until the first power-up looks right. Before powering up, check with a meter that PCA9685 VCC reads about 3.3 V, V+ about 5 V, and that the two are not shorted.

## Regenerate

[`3d_models/cad/desk_supermini.py`](3d_models/cad/desk_supermini.py) builds every export from the stock `Desk.step`. Board dimensions and placement are parameters at the top of the file. Measure your board's PCB thickness and BOOT position before printing the full desk. Needs FreeCAD 1.0:

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd mods/esp32-c3-supermini/3d_models/cad/desk_supermini.py
```

[`top_parts_supermini.py`](3d_models/cad/top_parts_supermini.py) builds `BootPusher`, `DeskTop`, `DeskPad` and `LampBase` from the stock parts:

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd mods/esp32-c3-supermini/3d_models/cad/top_parts_supermini.py
```

[`lamp_diffuser_clear.py`](3d_models/cad/lamp_diffuser_clear.py) builds `LampDiffuserClear` and `LampDiffuserClearSnug`:

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd mods/esp32-c3-supermini/3d_models/cad/lamp_diffuser_clear.py
```

[`assembly_supermini.py`](3d_models/cad/assembly_supermini.py) rebuilds the assembly STEP the same way:

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd mods/esp32-c3-supermini/3d_models/cad/assembly_supermini.py
```
