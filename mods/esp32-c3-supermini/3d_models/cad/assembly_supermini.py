"""Assembly preview: modified SG90 Desk with the ESP32-C3 SuperMini seated.

Run headless from the repo root:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        mods/esp32-c3-supermini/3d_models/cad/assembly_supermini.py

Writes DeskSuperMiniAssembly.step next to this file: the new Desk with the
SuperMini, the USB-C power breakout and the speaker seated, the modified
desk-top stack (DeskPad, DeskTop, LampBase) with the lamp (clear-resin
diffuser), the LED and the
BOOT pusher, with colours. Board component positions come from a published
SuperMini drawing and are approximate; only the outline, USB-C, buttons and
pins matter for fit.
"""

import os
import re

import FreeCAD
import Import
import Part

V = FreeCAD.Vector
HERE = os.path.dirname(os.path.abspath(__file__))

_top = {"__name__": "top_parts_supermini_lib", "__file__": os.path.join(HERE, "top_parts_supermini.py")}
exec(compile(open(_top["__file__"]).read(), _top["__file__"], "exec"), _top)
_lib = _top["L"]
_clear = {"__name__": "lamp_diffuser_clear_lib", "__file__": os.path.join(HERE, "lamp_diffuser_clear.py")}
exec(compile(open(_clear["__file__"]).read(), _clear["__file__"], "exec"), _clear)

X_USB, Y_C, Z_PT, Z_PB = _lib["X_USB"], _lib["Y_C"], _lib["Z_PT"], _lib["Z_PB"]
PCB_L, PCB_W = _lib["PCB_L"], _lib["PCB_W"]

BLACK = (0.08, 0.08, 0.09)
DESK = (0.72, 0.76, 0.84)
SILVER = (0.78, 0.79, 0.80)
GREY = (0.55, 0.56, 0.58)
DARK = (0.20, 0.20, 0.22)
GOLD = (0.85, 0.68, 0.25)
PINK = (0.91, 0.78, 0.76)
GREEN = (0.12, 0.55, 0.25)
ORANGE = (0.85, 0.42, 0.28)
TOP = (0.16, 0.16, 0.18)
FROST = (0.92, 0.93, 0.95)
RED = (0.85, 0.12, 0.10)


def comp(u0, u1, v0, v1, h):
    """Box on the component face. u from the USB edge, v towards the GPIO21 row,
    h towards the desk top."""
    return Part.makeBox(u1 - u0, v1 - v0, h, V(X_USB + u0, Y_C + v0, Z_PT - h))


def board_parts():
    parts = []

    pcb = Part.makeBox(PCB_L, PCB_W, Z_PB - Z_PT, V(X_USB, Y_C - PCB_W / 2, Z_PT))
    vertical = [e for e in pcb.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    parts.append(("PCB", pcb.makeFillet(0.8, vertical), BLACK))

    usb = comp(-0.93, 6.42, -4.47, 4.47, 3.26)
    long_edges = [e for e in usb.Edges if abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) > 1e-6]
    parts.append(("USB-C", usb.makeFillet(1.2, long_edges), SILVER))

    for name, v in (("BOOT", 2.5), ("RST", -2.5)):
        parts.append((name, comp(7.35, 10.35, v - 1.85, v + 1.85, 1.4), GREY))
        cap = Part.makeCylinder(1.0, 0.5, V(X_USB + 8.85, Y_C + v, Z_PT - 1.9))
        parts.append((name + " actuator", cap, DARK))

    qfn = Part.makeBox(5, 5, 0.9, V(-2.5, -2.5, 0))
    qfn.rotate(V(0, 0, 0), V(0, 0, 1), 45)
    qfn.translate(V(X_USB + 14.94, Y_C - 0.32, Z_PT - 0.9))
    parts.append(("ESP32-C3", qfn, DARK))
    parts.append(("Crystal", comp(16.5, 19.0, 2.77, 5.9, 0.8), SILVER))
    parts.append(("Antenna", comp(20.1, 22.3, -3.22, 3.23, 1.1), PINK))
    parts.append(("Regulator", comp(12.1, 13.67, 3.5, 6.38, 1.1), DARK))

    pin_u = [1.61 + 2.54 * k for k in range(8)]
    plastic = []
    pins = []
    for side in (-1, 1):
        v = side * 7.62
        plastic.append(Part.makeBox(pin_u[-1] - pin_u[0] + 2.54, 2.54, 2.5,
                                    V(X_USB + pin_u[0] - 1.27, Y_C + v - 1.27, Z_PB)))
        for u in pin_u:
            pins.append(Part.makeBox(0.64, 0.64, 2.0 + (Z_PB - Z_PT) + 2.5 + 6.0,
                                     V(X_USB + u - 0.32, Y_C + v - 0.32, Z_PT - 2.0)))
    parts.append(("Header plastic", Part.makeCompound(plastic), BLACK))
    parts.append(("Header pins", Part.makeCompound(pins), GOLD))
    return parts


def power_parts():
    g = _lib
    x_edge, y_c, z_lo, t = g["P_X_EDGE"], g["P_Y_C"], g["P_Z_PCB_LO"], g["P_PCB_T"]
    pcb = Part.makeBox(g["P_PCB_L"], g["P_PCB_W"], t, V(x_edge, y_c - g["P_PCB_W"] / 2, z_lo))
    for hx, hy in g["power_holes"]():
        pcb = pcb.cut(Part.makeCylinder(1.5, t + 2, V(hx, hy, z_lo - 1)))
    usb = Part.makeBox(g["P_USB_LEN"], g["USB_W"], g["USB_H"],
                       V(g["P_X_FRONT"], y_c - g["USB_W"] / 2, g["P_Z_USB"] - g["USB_H"] / 2))
    long_edges = [e for e in usb.Edges if abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) > 1e-6]
    screws = [Part.makeCylinder(2.75, 2.0, V(hx, hy, z_lo + t)).fuse(
              Part.makeCylinder(1.2, 6.0, V(hx, hy, z_lo + t - 6.0)))  # core only; threads cut the pilot
              for hx, hy in g["power_holes"]()]
    return [("Power PCB", pcb, GREEN), ("Power USB-C", usb.makeFillet(1.2, long_edges), SILVER),
            ("M3x6 screws", Part.makeCompound(screws), SILVER)]


def speaker_part():
    g = _lib
    cx, cy = g["SPK_C"]
    front = g["SPK_SEAT_Z"] + g["SPK_RIM_H"]
    cone = Part.makeCone(g["SPK_D"] / 2 - 1.2, 3.0, 1.0, V(cx, cy, front - 1.0))
    return g["speaker_body"]().cut(cone)


def top_parts():
    """Desk-top stack, lamp, LED and BOOT pusher in the Desk frame."""
    t = _top
    lx, ly = _lib["LED"]
    parts = [
        ("DeskPad", t["to_desk"](t["build_deskpad"](), "DeskPad"), ORANGE),
        ("DeskTop", t["to_desk"](t["build_desktop"](), "DeskTop"), TOP),
        ("LampBase", t["to_desk"](t["build_lampbase"](), "LampBase"), ORANGE),
        ("BootPusher", t["pusher_desk"](), ORANGE),
    ]
    z_top = -(t["DESKPAD_T"] + t["DESKTOP_T"])
    # Clear-resin light pipe: shoulder on the DeskTop rim, spigot down the light hole.
    diffuser = _clear["in_desk"](_clear["build"]())
    cap = t["read"]("LampCap")
    cap.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    cap.translate(V(lx, ly, z_top - _clear["ROD_LEN"] + _clear["CAP_SOCKET"]))
    parts += [("LampDiffuserClear", diffuser, FROST), ("LampCap", cap, ORANGE)]

    # 5 mm LED pushed in from the cavity: dome flush with the desk top, flange on the tube end.
    depth = _lib["LED_DEPTH"]
    led = Part.makeSphere(2.5, V(lx, ly, 2.5)).common(Part.makeBox(6, 6, 2.5, V(lx - 3, ly - 3, 0)))
    led = led.fuse([Part.makeCylinder(2.5, depth - 2.5, V(lx, ly, 2.5)),
                    Part.makeCylinder(2.9, 1.0, V(lx, ly, depth))])
    legs = [Part.makeBox(0.5, 0.5, 12, V(lx + dx - 0.25, ly - 0.25, depth + 1.0)) for dx in (-1.27, 1.27)]
    parts += [("LED", led, RED), ("LED legs", Part.makeCompound(legs), SILVER)]
    return parts


def add_step_colours(path, colours):
    """Append AP214 surface colours to every solid, keyed by product name.

    FreeCAD's console build exports no colours, so the styles are written here.
    """
    text = open(path).read()
    head, data = text.split("DATA;", 1)
    data, tail = data.split("ENDSEC;", 1)
    entities = [e.strip() for e in data.split(";") if e.strip()]
    next_id = max(int(m) for m in re.findall(r"#(\d+)\s*=", data)) + 1

    product, brep_owner, brep_context = None, {}, {}
    for e in entities:
        m = re.match(r"#(\d+)\s*=\s*PRODUCT\('([^']*)'", e)
        if m:
            product = m.group(2)
            continue
        m = re.match(r"#(\d+)\s*=\s*MANIFOLD_SOLID_BREP\(", e)
        if m and product is not None:
            # Compound members come out as "Name001", "Name002", ...
            brep_owner[m.group(1)] = re.sub(r"\d{3}$", "", product)
        m = re.match(r"#\d+\s*=\s*[A-Z_]*SHAPE_REPRESENTATION\('[^']*',\s*\(([^)]*)\),\s*#(\d+)\)", e, re.S)
        if m:
            for ref in re.findall(r"#(\d+)", m.group(1)):
                brep_context[ref] = m.group(2)

    out = []
    for brep, name in brep_owner.items():
        if name not in colours:
            continue
        r, g, b = colours[name]
        i = next_id
        next_id += 9
        out += [
            f"#{i} = COLOUR_RGB('',{r:.4f},{g:.4f},{b:.4f})",
            f"#{i + 1} = FILL_AREA_STYLE_COLOUR('',#{i})",
            f"#{i + 2} = FILL_AREA_STYLE('',(#{i + 1}))",
            f"#{i + 3} = SURFACE_STYLE_FILL_AREA(#{i + 2})",
            f"#{i + 4} = SURFACE_SIDE_STYLE('',(#{i + 3}))",
            f"#{i + 5} = SURFACE_STYLE_USAGE(.BOTH.,#{i + 4})",
            f"#{i + 6} = PRESENTATION_STYLE_ASSIGNMENT((#{i + 5}))",
            f"#{i + 7} = STYLED_ITEM('color',(#{i + 6}),#{brep})",
            f"#{i + 8} = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(#{i + 7}),#{brep_context[brep]})",
        ]

    data = data.rstrip() + "\n" + "".join(e + ";\n" for e in out)
    open(path, "w").write(head + "DATA;" + data + "ENDSEC;" + tail)


def main():
    desk, _ = _lib["build"]()
    doc = FreeCAD.newDocument("DeskSuperMiniAssembly")

    desk_obj = doc.addObject("Part::Feature", "Desk")
    desk_obj.Shape = desk
    board = doc.addObject("App::Part", "ESP32_C3_SuperMini")
    colours = {"Desk": DESK}
    for label, shape, colour in board_parts():
        o = doc.addObject("Part::Feature", "Board")
        o.Label = label
        o.Shape = shape
        board.addObject(o)
        colours[label] = colour
    power = doc.addObject("App::Part", "USB_C_power_breakout")
    for label, shape, colour in power_parts():
        o = doc.addObject("Part::Feature", "Power")
        o.Label = label
        o.Shape = shape
        power.addObject(o)
        colours[label] = colour
    speaker = doc.addObject("Part::Feature", "Speaker")
    speaker.Shape = speaker_part()
    colours["Speaker"] = DARK
    top = doc.addObject("App::Part", "Desk_top_stack")
    for label, shape, colour in top_parts():
        o = doc.addObject("Part::Feature", "Top")
        o.Label = label
        o.Shape = shape
        top.addObject(o)
        colours[label] = colour
    doc.recompute()

    step = os.path.join(HERE, "DeskSuperMiniAssembly.step")
    Import.export([desk_obj, board, power, speaker, top], step)
    add_step_colours(step, colours)
    FreeCAD.closeDocument(doc.Name)


if __name__ in ("__main__", "assembly_supermini"):
    main()
