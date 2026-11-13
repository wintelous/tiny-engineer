"""Solid light-pipe LampDiffuser for clear resin (SLA / MSLA).

Run headless from the repo root:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        mods/esp32-c3-supermini/3d_models/cad/lamp_diffuser_clear.py

Writes LampDiffuserClear (0.15 mm clearance on the rod, 0.2 mm on the spigot)
and LampDiffuserClearSnug (0.1 mm everywhere) next to the other mod exports.

The stock LampDiffuser is a thin FDM tube that the C3-Zero LED lit from right
below. With the SuperMini mod the 5 mm LED sits 5 mm lower, under DeskPad and
DeskTop. This part is a solid clear rod instead:

- a spigot drops through the DeskTop light hole to just above the LED dome and
  collects its light;
- the rod carries it up by total internal reflection;
- six helical round grooves in the visible stretch between LampBase and LampCap
  break that reflection, so the light leaks out along glowing spiral lines,
  like a filament.

Part frame: z = 0 is the shoulder that rests on DeskTop, the rod goes up to
z = 20 (inside LampCap), the spigot goes down to z = -SPIGOT_LEN.
"""

import os

import FreeCAD
import Part

V = FreeCAD.Vector
HERE = os.path.dirname(os.path.abspath(__file__))

_top = {"__name__": "top_parts_supermini_lib", "__file__": os.path.join(HERE, "top_parts_supermini.py")}
exec(compile(open(_top["__file__"]).read(), _top["__file__"], "exec"), _top)
L = _top["L"]

# --- Fit ---------------------------------------------------------------------------
BORE_R = 3.5            # LampBase bore and LampCap socket
ROD_R = 3.35            # 0.15 mm clearance, like the stock LampDiffuser
ROD_LEN = 20.0
BASE_H = 6.0            # LampBase height: the rod is hidden below this
CAP_SOCKET = 2.0        # LampCap socket depth: hidden above ROD_LEN - this
END_CHAMFER = 0.3       # also takes up the first-layer flare on the plate end

# --- Light input ----------------------------------------------------------------------
# DeskPad (1.5) + DeskTop (3.5) between the shoulder and the desk top, where the
# LED dome sits flush. Stop short of the dome so a proud LED does not lift the lamp.
LIGHT_HOLE = _top["LIGHT_HOLE"]  # DeskTop, 5.2
SPIGOT_D = 4.8          # 0.2 mm clearance in the light hole
SPIGOT_GAP = 0.4        # spigot end to the top of the LED dome
SPIGOT_LEN = _top["DESKPAD_T"] + _top["DESKTOP_T"] - SPIGOT_GAP

# --- Glow ---------------------------------------------------------------------------
GROOVES = 6
GROOVE_R = 0.5          # round groove, swept along a helix
GROOVE_DEPTH = 0.45     # into the rod surface; 1.0 mm wide at the surface
TWIST = 180.0           # degrees over the grooved stretch
GROOVE_Z0 = BASE_H + 0.8   # groove ends are rounded, so keep them clear of
GROOVE_Z1 = ROD_LEN - CAP_SOCKET - 0.8  # LampBase and LampCap


# Exports: name -> (rod radius, spigot diameter). The snug one has 0.1 mm
# clearance in the LampBase bore, the LampCap socket and the DeskTop light hole.
VARIANTS = {
    "LampDiffuserClear": (ROD_R, SPIGOT_D),
    "LampDiffuserClearSnug": (BORE_R - 0.1, LIGHT_HOLE - 0.2),
}


def groove(angle, rod_r=ROD_R):
    """One helical groove cutter: a tube along a helix with ball ends."""
    rc = rod_r + GROOVE_R - GROOVE_DEPTH
    height = GROOVE_Z1 - GROOVE_Z0
    pitch = height * 360.0 / TWIST
    helix = Part.makeHelix(pitch, height, rc)
    start = helix.Edges[0].valueAt(helix.Edges[0].FirstParameter)
    end = helix.Edges[-1].valueAt(helix.Edges[-1].LastParameter)
    tangent = helix.Edges[0].tangentAt(helix.Edges[0].FirstParameter)
    profile = Part.Wire(Part.makeCircle(GROOVE_R, start, tangent))
    tube = Part.Wire(helix.Edges).makePipeShell([profile], True, True)
    cutter = tube.fuse([Part.makeSphere(GROOVE_R, start), Part.makeSphere(GROOVE_R, end)])
    cutter.translate(V(0, 0, GROOVE_Z0))
    cutter.rotate(V(0, 0, 0), V(0, 0, 1), angle)
    return cutter


def build(rod_r=ROD_R, spigot_d=SPIGOT_D):
    rod = Part.makeCylinder(rod_r, ROD_LEN)
    spigot = Part.makeCylinder(spigot_d / 2, SPIGOT_LEN + 0.01, V(0, 0, -SPIGOT_LEN))
    body = rod.fuse(spigot).removeSplitter()
    ends = [e for e in body.Edges
            if e.Curve.__class__.__name__ == "Circle"
            and (abs(e.Curve.Center.z - ROD_LEN) < 1e-6 or abs(e.Curve.Center.z + SPIGOT_LEN) < 1e-6)]
    body = body.makeChamfer(END_CHAMFER, ends)
    for k in range(GROOVES):
        body = body.cut(groove(k * 360.0 / GROOVES, rod_r))
    return body.removeSplitter()


def in_desk(shape):
    """Place the part in the Desk frame: shoulder on DeskTop, rod up (towards -z)."""
    s = shape.copy()
    s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    lx, ly = L["LED"]
    s.translate(V(lx, ly, -(_top["DESKPAD_T"] + _top["DESKTOP_T"])))
    return s


if __name__ in ("__main__", "lamp_diffuser_clear"):
    for name, (rod_r, spigot_d) in VARIANTS.items():
        part = build(rod_r, spigot_d)
        if not part.isValid() or len(part.Solids) != 1:
            raise SystemExit(f"{name}: valid={part.isValid()} solids={len(part.Solids)}")
        L["export"](part, name)
        print(f"{name}: rod {2 * rod_r:.2f} mm, spigot {spigot_d:.2f} mm, volume {part.Volume:.1f} mm3")
