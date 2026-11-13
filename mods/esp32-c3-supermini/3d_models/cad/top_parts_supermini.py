"""BOOT pusher and the desk-top parts that change with the SuperMini Desk.

Run headless from the repo root:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        mods/esp32-c3-supermini/3d_models/cad/top_parts_supermini.py

Inputs are the stock DeskTop, DeskPad and LampBase STEP files. Outputs go next
to the Desk exports: BootPusher, DeskTop, DeskPad, LampBase.

Frames, from the stock exports and the hole patterns they share:
- DeskTop: Desk turned 180 degrees about x (y and z flip), z = 0 on DeskPad.
- DeskPad: DeskTop shifted 2 mm along +x, z = 0 on the Desk.
- LampBase: DeskTop shifted 0.35 mm along +x and 55.95 mm along -y, z = 0 on DeskTop.
The stack on the desk top is DeskPad (1.5 mm), DeskTop (3.5 mm), then LampBase.
"""

import os

import FreeCAD
import Part

V = FreeCAD.Vector
HERE = os.path.dirname(os.path.abspath(__file__))

_lib = {"__name__": "desk_supermini_lib", "__file__": os.path.join(HERE, "desk_supermini.py")}
exec(compile(open(_lib["__file__"]).read(), _lib["__file__"], "exec"), _lib)
L = _lib
STOCK = os.path.join(L["REPO"], "3d_models", "parts", "sg90", "step")

# --- Stack ------------------------------------------------------------------------
DESKPAD_T = 1.5
DESKTOP_T = 3.5             # plate thickness away from the bell ring
DESKTOP_X, LAMP_X, LAMP_Y = 0.0, 0.35, -55.95   # see the frames above
DESKPAD_X = 2.0

# --- BOOT pusher ------------------------------------------------------------------
BOOT_H = 1.9                # button top (actuator) above the PCB component face; measure yours
PIN_D = 2.5                 # through the 3.0 mm guide bore
COLLAR_D, COLLAR_T = 4.0, 1.0  # under the guide tube: keeps the pin from leaving through the top
PROTRUDE = 1.5              # above the DeskTop surface while the pin rests on the button
TOP_CHAMFER = 0.4
NECK = 0.2                  # cone between collar and pin, small enough to stay out of the bore
TOP_HOLE = 3.2              # DeskTop and DeskPad
TOP_HOLE_CHAMFER = 0.5

# --- Lamp ---------------------------------------------------------------------------
LIGHT_HOLE = 5.2            # DeskTop, over the LED; LampDiffuser (6.7 mm) rests on its rim
C3_OPENING = (-13.1, 13.4, 46.2, 65.7)  # stock DeskTop cut for the C3-Zero, closed
LAMP_BUTTON = (0.05, -5.35, 1.75)       # stock LampBase hole for LampButton, closed


def desk_to_top(x, y):
    return x - DESKTOP_X, -y


def desk_to_pad(x, y):
    return x + DESKPAD_X, -y


def boot_xy():
    return L["X_USB"] + L["BOOT_FROM_USB_EDGE"], L["Y_C"] + L["BOOT_FROM_AXIS"]


def pusher_z():
    """Desk-frame z of the pusher: (bottom on the button, collar top, top end)."""
    bottom = L["Z_PT"] - BOOT_H
    top = -(DESKPAD_T + DESKTOP_T) - PROTRUDE
    return bottom, bottom - COLLAR_T, top


def read(name):
    s = Part.Shape()
    s.read(os.path.join(STOCK, name + ".step"))
    return s.Solids[0] if len(s.Solids) == 1 else s


def chamfered_hole(x, y, d, depth, chamfer):
    """Vertical hole from z = -1 to depth, with a chamfer at z = depth."""
    hole = Part.makeCylinder(d / 2, depth + 2, V(x, y, -1))
    cone = Part.makeCone(d / 2, d / 2 + chamfer + 1, chamfer + 1, V(x, y, depth - chamfer))
    return hole.fuse(cone)


def build_pusher():
    """BootPusher in its print frame: collar on the bed, pin up."""
    bottom, _, top = pusher_z()
    length = bottom - top
    collar = Part.makeCylinder(COLLAR_D / 2, COLLAR_T)
    neck = Part.makeCone(PIN_D / 2 + NECK, PIN_D / 2, NECK, V(0, 0, COLLAR_T))
    pin = Part.makeCylinder(PIN_D / 2, length - COLLAR_T - TOP_CHAMFER, V(0, 0, COLLAR_T))
    tip = Part.makeCone(PIN_D / 2, PIN_D / 2 - TOP_CHAMFER, TOP_CHAMFER, V(0, 0, length - TOP_CHAMFER))
    return collar.fuse([neck, pin, tip]).removeSplitter()


def build_desktop():
    top = read("DeskTop")
    x0, x1, y0, y1 = C3_OPENING
    top = top.fuse(Part.makeBox(x1 - x0, y1 - y0, DESKTOP_T, V(x0, y0, 0)))
    lx, ly = desk_to_top(*L["LED"])
    px, py = desk_to_top(*boot_xy())
    top = top.cut(Part.makeCylinder(LIGHT_HOLE / 2, DESKTOP_T + 2, V(lx, ly, -1)))
    top = top.cut(chamfered_hole(px, py, TOP_HOLE, DESKTOP_T, TOP_HOLE_CHAMFER))
    return top.removeSplitter()


def build_deskpad():
    pad = read("DeskPad")
    px, py = desk_to_pad(*boot_xy())
    pad = pad.cut(Part.makeCylinder(TOP_HOLE / 2, DESKPAD_T + 2, V(px, py, -1)))
    return pad.removeSplitter()


def build_lampbase():
    """Close the LampButton hole with the material mirrored from the other side."""
    base = read("LampBase")
    x, y, r = LAMP_BUTTON
    plug = Part.makeCylinder(r + 0.01, 10, V(x, y, -1))
    # Mirrored as a compound: a mirrored bare solid comes out inside-out and
    # its common with the plug is empty.
    mirrored = Part.makeCompound([base]).mirror(V(0, 0, 0), V(0, 1, 0))
    return base.fuse(mirrored.common(plug)).removeSplitter()


def to_desk(shape, name):
    """Move a stock-frame part (or its modified copy) into the Desk frame."""
    s = shape.copy()
    s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    if name == "DeskTop":
        s.translate(V(DESKTOP_X, 0, -DESKPAD_T))
    elif name == "DeskPad":
        s.translate(V(-DESKPAD_X, 0, 0))
    elif name == "LampBase":
        s.translate(V(-LAMP_X, LAMP_Y, -(DESKPAD_T + DESKTOP_T)))
    return s


def pusher_desk():
    """BootPusher placed in the Desk frame, resting on the button."""
    p = build_pusher()
    p.rotate(V(0, 0, 0), V(1, 0, 0), 180)  # pin now towards -z, collar face at z = 0
    bx, by = boot_xy()
    p.translate(V(bx, by, pusher_z()[0]))
    return p


def check(shape, name):
    if not shape.isValid() or len(shape.Solids) != 1:
        raise SystemExit(f"{name}: valid={shape.isValid()} solids={len(shape.Solids)}")


if __name__ in ("__main__", "top_parts_supermini"):
    parts = {
        "BootPusher": build_pusher(),
        "DeskTop": build_desktop(),
        "DeskPad": build_deskpad(),
        "LampBase": build_lampbase(),
    }
    for name, shape in parts.items():
        check(shape, name)
        L["export"](shape, name)
    bottom, collar_top, top = pusher_z()
    print(f"BootPusher length {bottom - top:.2f} mm, collar {collar_top - L['PUSHER_TUBE_BOTTOM']:.2f} mm "
          f"below the guide tube")
