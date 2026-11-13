"""Build the SG90 Desk for an ESP32-C3 SuperMini mounted in the USB corner.

Run headless from the repo root:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        mods/esp32-c3-supermini/3d_models/cad/desk_supermini.py

Input is the stock 3d_models/parts/sg90/step/Desk.step. Output goes to
mods/esp32-c3-supermini/3d_models/parts/sg90/{step,stl,3mf}/.

Desk frame (stock export): z = 0 is the desk top face (print bed side),
the cavity opens towards +z, x = -38.9 is the outer face of the USB wall,
y = -72.7 is the outer face of the slatted end wall.

The board hangs with its component side (USB-C, BOOT/RST) facing the desk
top and its header pins facing the open cavity.
"""

import math
import os

import FreeCAD
import Mesh
import Part

V = FreeCAD.Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SRC = os.path.join(REPO, "3d_models", "parts", "sg90", "step", "Desk.step")
OUT = os.path.join(REPO, "mods", "esp32-c3-supermini", "3d_models", "parts", "sg90")

# --- Board (ESP32-C3 SuperMini, 22.52 x 18 mm) -------------------------------
PCB_L = 22.52          # along x, USB end at the wall
PCB_W = 18.0           # along y
PCB_T = 1.0            # measure yours; the hooks tolerate about 0.8 to 1.2
USB_OVERHANG = 0.93    # receptacle front past the PCB edge
USB_W, USB_H, USB_LEN = 8.94, 3.26, 7.35
BOOT_FROM_USB_EDGE = 8.8   # button centre, along x
BOOT_FROM_AXIS = 2.7       # button centre, towards +y (the GPIO21 pin row)

# --- Placement ----------------------------------------------------------------
WALL_IN = -36.9        # inner face of the USB wall
WALL_OUT = -38.9
GAP = 0.2              # PCB edge to wall
Y_C = -57.95           # board axis; stock opening was at -59.1, the corner boss forced the shift
Z_USB = 13.7           # receptacle centre, same height as the stock opening

X_USB = WALL_IN + GAP              # PCB edge at the USB end
X_FAR = X_USB + PCB_L              # antenna end
Z_PT = Z_USB + USB_H / 2           # PCB component face (towards the desk top)
Z_PB = Z_PT + PCB_T                # PCB pin face (towards the cavity)

# --- Stock features touched ---------------------------------------------------
OLD_HOLE_Y, OLD_HOLE_Z = -59.1, 13.7
HOLE_W, HOLE_H, HOLE_R = 10.0, 4.0, 1.5        # through the wall
RECESS_W, RECESS_H, RECESS_R, RECESS_D = 14.0, 8.0, 3.0, 0.5  # outer counterbore
PLATE_TOP = 2.0
BLOCK = (-26.85, -13.15, -65.3, -46.6)  # stock plateau (x0, x1, y0, y1), removed
BLOCK_TOP = 10.0
LAMP_SCREW = (-15.4, -55.95)       # stock LampBase pilot through the plate, kept
SLOTS = (-12.95, 12.75, -65.25, -46.65)  # stock C3-Zero pin slots (x0, x1, y0, y1), filled
BOSS_TRIM_Y = -67.2    # corner boss (BottomCover / DeskTop screw) face after trimming

# --- New features ---------------------------------------------------------------
BAND_IN, BAND_OUT = 5.1, 8.6       # clip bands, |y - Y_C|, clear of antenna, pin rows and screw boss
STOP_X0 = X_FAR - 1.9              # finger tops under the component face
STOP_X1 = X_FAR - 0.45
REST_FINGER_Z = 12.5               # full-width rest below this; components start at about 13.3
REST_X_BASE = -22.0                # rest footprint on the desk top, 45 degree flank
CLIP_X0 = X_FAR + 0.1              # clip post inner face
CLIP_T_BASE, CLIP_T_TOP = 2.4, 1.6  # clip post tapers towards the hook
LIP = 0.9                          # reach of the hook over the PCB
LIP_T = 1.0
LIP_GAP = 0.1                      # PCB thickness allowance
CLIP_GAP = 0.55                    # free space around each clip post
BACK_WALL_GAP = 0.15               # antenna edge of the PCB to the back wall
BACK_WALL_T = 4.0
LEDGE_HALF_W = 2.6                 # receptacle rest, across y
LEDGE_X1 = WALL_IN + 4.7
PUSHER_BORE = 3.0
PUSHER_OD = 6.0
PUSHER_TUBE_BOTTOM = 11.0          # leaves about 2 mm above the button
SCREW_WALL = 1.5                   # around the LampBase screw pilot
LED = (1.90, -55.95)               # under the lamp opening (LampBase (2.25, 0), turned like DeskTop)
LED_HOLE = 5.1                     # 5 mm LED body
LED_DEPTH = 7.5                    # LED inserted from the cavity; flange stops here, dome flush with the top
LED_WALL = 1.5

# --- USB-C power breakout (other end of the same wall) ---------------------------
# Generic green 24-pin USB-C female breakout with two M3 holes, lying flat.
P_PCB_L, P_PCB_W, P_PCB_T = 10.2, 20.5, 1.6   # along x, along y; thickness: measure yours
P_USB_LEN = 10.8
P_USB_PAST_EDGE = 11.3      # shell front to PCB edge, from the printed fit test
P_HOLE_H = 3.5              # opening height (the SuperMini side keeps HOLE_H)
P_USB_ABOVE = 0.0           # shell centre above the PCB mid-plane (0 for a board-edge straddle connector)
P_HOLE_PITCH, P_HOLE_FROM_EDGE = 15.6, 2.6
P_Y_C = 59.3                # clear of the chair-arm wall (48.7) and the slatted end wall (70.7)
END_WALL_IN = 70.7          # inner face of the slatted end wall at this end
P_Z_USB = Z_USB             # same height as the SuperMini port
P_X_FRONT = WALL_OUT + RECESS_D    # shell front at the recess floor
P_X_EDGE = P_X_FRONT + P_USB_PAST_EDGE
P_Z_PCB_LO = P_Z_USB - P_USB_ABOVE - P_PCB_T / 2
P_BOSS_OD = 6.5
P_PILOT = 2.5               # M3 thread-forming into PLA/PETG
P_PILOT_DEPTH = 7.0         # M3x6 through the PCB bites about 4.4 mm
OLD_PAD = (-38.9, -31.4, 53.3, 66.1, 10.1, 38.1)  # stock 5993 slot and M2 holes, filled

# --- Round speaker (20 mm), flat under the desk top ------------------------------
SPK_C = (3.5, -26.0)        # open desk top between the LED tube and the desk centre hole
SPK_D = 20.0
SPK_RIM_H = 2.4             # rim thickness; the full 3.25 mm is only at the centre bump on the back
SPK_BUMP_D, SPK_BUMP_H = 10.9, 0.85  # magnet bump on the back
SPK_SEAT_Z = 10.85          # back face of the rim; the bump hangs between the pads
SPK_ANGLES = (60, 180, 300)     # no snap facing the rail
SPK_PAD = (8.4, 9.6, 4.0)   # radial from, radial to, width: touches the rim edge, outside the vent holes
SPK_PAD_BASE_R0 = 6.0       # pad widens inward below the bump
SPK_PAD_TOP_H = 1.5         # height of the narrow contact part
SPK_GAP = 0.2               # radial, speaker edge to snap
SPK_POST_W = 6.5            # arc length at the inner face
SPK_POST_T_BASE, SPK_POST_T_TOP = 2.0, 1.2
SPK_ROOT_FILLET = 1.0       # outside the post where it meets the desk top
SPK_LIP, SPK_LIP_T = 0.6, 0.8
PAD_FACE = -31.4            # inner face of the thick wall section at this end


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def rounded_slot_x(x0, x1, yc, zc, w, h, r):
    """Rounded rectangle in the YZ plane, extruded along x."""
    b = box(x0, x1, yc - w / 2, yc + w / 2, zc - h / 2, zc + h / 2)
    edges = [e for e in b.Edges if abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) > 1e-6]
    return b.makeFillet(r, edges)


def xz_profile(points, y0, y1):
    """Closed polygon in the XZ plane at y0, extruded to y1."""
    pts = [V(x, y0, z) for x, z in points]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, y1 - y0, 0))


def band_ranges(lo, hi):
    return [(Y_C + lo, Y_C + hi), (Y_C - hi, Y_C - lo)]


def speaker_holder():
    """Three pads and three snaps around SPK_C, as one list of solids."""
    r_in = SPK_D / 2 + SPK_GAP
    z0 = PLATE_TOP - 0.01
    z_lip0 = SPK_SEAT_Z + SPK_RIM_H + 0.1
    z_lip1 = z_lip0 + SPK_LIP_T
    z_top = z_lip1 + SPK_LIP
    span = math.degrees(SPK_POST_W / r_in)
    up = V(0, 0, 1)

    def ring(r0, r1, za, zb):
        o = V(0, 0, za)
        return Part.makeCylinder(r1, zb - za, o, up, span).cut(Part.makeCylinder(r0, zb - za, o, up, span))

    r_root = r_in + SPK_POST_T_BASE
    post = Part.makeCone(r_root, r_in + SPK_POST_T_TOP, z_top - z0, V(0, 0, z0), up, span)
    root = Part.makeCone(r_root + SPK_ROOT_FILLET, r_root, SPK_ROOT_FILLET, V(0, 0, z0), up, span)
    post = post.fuse(root).cut(Part.makeCylinder(r_in, z_top, V(0, 0, 0), up, span))
    lip = ring(r_in - SPK_LIP, r_in + 0.01, z_lip0, z_lip1)
    lead_in = Part.makeCylinder(r_in + 0.01, SPK_LIP, V(0, 0, z_lip1), up, span).cut(
        Part.makeCone(r_in - SPK_LIP, r_in, SPK_LIP, V(0, 0, z_lip1), up, span))
    snap = post.fuse([lip, lead_in])
    snap.rotate(V(0, 0, 0), up, -span / 2)

    pr0, pr1, pw = SPK_PAD
    z_step = SPK_SEAT_Z - SPK_PAD_TOP_H
    pad = box(pr0, pr1, -pw / 2, pw / 2, z_step - 0.01, SPK_SEAT_Z).fuse(
        box(SPK_PAD_BASE_R0, pr1, -pw / 2, pw / 2, z0, z_step))

    out = []
    for a in SPK_ANGLES:
        for s in (snap, pad):
            s = s.copy()
            s.rotate(V(0, 0, 0), up, a)
            s.translate(V(SPK_C[0], SPK_C[1], 0))
            out.append(s)
    return out


def speaker_body():
    """Speaker envelope: rim plus the bump on the back."""
    rim = Part.makeCylinder(SPK_D / 2, SPK_RIM_H, V(SPK_C[0], SPK_C[1], SPK_SEAT_Z))
    bump = Part.makeCylinder(SPK_BUMP_D / 2, SPK_BUMP_H + 0.01,
                             V(SPK_C[0], SPK_C[1], SPK_SEAT_Z - SPK_BUMP_H))
    return rim.fuse(bump)


def power_holes():
    x = P_X_EDGE + P_HOLE_FROM_EDGE
    return [(x, P_Y_C - P_HOLE_PITCH / 2), (x, P_Y_C + P_HOLE_PITCH / 2)]


def build():
    desk = Part.Shape()
    desk.read(SRC)
    desk = desk.Solids[0] if len(desk.Solids) == 1 else desk

    pre_cut, add, cut = [], [], []

    # USB opening: fill the stock one, cut a new one on the board axis.
    add.append(box(WALL_OUT, WALL_IN,
                   OLD_HOLE_Y - RECESS_W / 2, OLD_HOLE_Y + RECESS_W / 2,
                   OLD_HOLE_Z - RECESS_H / 2, OLD_HOLE_Z + RECESS_H / 2))
    cut.append(rounded_slot_x(WALL_OUT - 1, WALL_IN + 0.01, Y_C, Z_USB, HOLE_W, HOLE_H, HOLE_R))
    cut.append(rounded_slot_x(WALL_OUT - 1, WALL_OUT + RECESS_D, Y_C, Z_USB,
                              RECESS_W, RECESS_H, RECESS_R))

    # Corner boss: shave the face towards the board, full height.
    cut.append(box(WALL_IN, -32.0, BOSS_TRIM_Y, -66.0, PLATE_TOP, 46.2))

    # Rest under the USB receptacle shell.
    add.append(box(WALL_IN, LEDGE_X1, Y_C - LEDGE_HALF_W, Y_C + LEDGE_HALF_W,
                   PLATE_TOP - 0.01, Z_PT - USB_H))

    # Stock plateau (main control board seat): not needed with discrete boards.
    bx0, bx1, by0, by1 = BLOCK
    pre_cut.append(box(bx0, bx1, by0, by1, PLATE_TOP, BLOCK_TOP + 0.05))

    # Far end: one rest across the board width, tapering up to two fingers that
    # touch the PCB clear of the antenna and the pin rows.
    rest = xz_profile([(STOP_X1, PLATE_TOP - 0.01), (STOP_X1, REST_FINGER_Z),
                       (STOP_X0, REST_FINGER_Z),
                       (REST_X_BASE, REST_FINGER_Z - (STOP_X0 - REST_X_BASE)),
                       (REST_X_BASE, PLATE_TOP - 0.01)],
                      Y_C - BAND_OUT, Y_C + BAND_OUT)
    add.append(rest)
    add.append(Part.makeCylinder(1.05 + SCREW_WALL, REST_FINGER_Z - PLATE_TOP + 0.01,
                                 V(LAMP_SCREW[0], LAMP_SCREW[1], PLATE_TOP - 0.01)))
    cut.append(Part.makeCylinder(1.05, BLOCK_TOP + 1, V(LAMP_SCREW[0], LAMP_SCREW[1], -1)))

    # Stock C3-Zero pin slots closed; one 5 mm LED under the lamp instead.
    sx0, sx1, sy0, sy1 = SLOTS
    add.append(box(sx0, sx1, sy0, sy1, 0, PLATE_TOP))
    add.append(Part.makeCylinder(LED_HOLE / 2 + LED_WALL, LED_DEPTH - PLATE_TOP + 0.01,
                                 V(LED[0], LED[1], PLATE_TOP - 0.01)))
    cut.append(Part.makeCylinder(LED_HOLE / 2, LED_DEPTH + 1, V(LED[0], LED[1], -1)))

    z_lip0 = Z_PB + LIP_GAP
    z_lip1 = z_lip0 + LIP_T
    z_top = z_lip1 + LIP
    for y0, y1 in band_ranges(BAND_IN, BAND_OUT):
        add.append(box(STOP_X0, STOP_X1, y0, y1, REST_FINGER_Z - 0.01, Z_PT))
        # Clip post: tapered so it is stiff at the root and still flexes.
        add.append(xz_profile([(CLIP_X0, PLATE_TOP - 0.01), (CLIP_X0 + CLIP_T_BASE, PLATE_TOP - 0.01),
                               (CLIP_X0 + CLIP_T_TOP, z_top), (CLIP_X0, z_top)], y0, y1))
        add.append(box(CLIP_X0 - LIP, CLIP_X0 + 0.01, y0, y1, z_lip0, z_lip1))
        add.append(xz_profile([(CLIP_X0 - LIP, z_lip1), (CLIP_X0 + 0.01, z_lip1),
                               (CLIP_X0 + 0.01, z_top)], y0, y1))

    # Back wall between the clips: takes the push of a USB-C plug instead of the
    # clips. Joined to the rest below the component face.
    wy = BAND_IN - CLIP_GAP
    wall_x0 = X_FAR + BACK_WALL_GAP
    add.append(box(wall_x0, wall_x0 + BACK_WALL_T, Y_C - wy, Y_C + wy, PLATE_TOP - 0.01, z_top))
    add.append(box(STOP_X1 - 0.01, wall_x0 + 0.01, Y_C - wy, Y_C + wy, PLATE_TOP - 0.01, REST_FINGER_Z))

    # BOOT pusher guide through the desk top.
    bx = X_USB + BOOT_FROM_USB_EDGE
    by = Y_C + BOOT_FROM_AXIS
    add.append(Part.makeCylinder(PUSHER_OD / 2, PUSHER_TUBE_BOTTOM - PLATE_TOP + 0.01,
                                 V(bx, by, PLATE_TOP - 0.01)))
    cut.append(Part.makeCylinder(PUSHER_BORE / 2, PUSHER_TUBE_BOTTOM + 2, V(bx, by, -1)))

    # USB-C power breakout: fill the stock 5993 slot and screw holes, cut a
    # horizontal opening through the thick wall, two M3 bosses from the desk top.
    ox0, ox1, oy0, oy1, oz0, oz1 = OLD_PAD
    add.append(box(ox0, ox1, oy0, oy1, oz0, oz1))
    cut.append(rounded_slot_x(WALL_OUT - 1, PAD_FACE + 0.01, P_Y_C, P_Z_USB, HOLE_W, P_HOLE_H, HOLE_R))
    cut.append(rounded_slot_x(WALL_OUT - 1, WALL_OUT + RECESS_D, P_Y_C, P_Z_USB,
                              RECESS_W, RECESS_H, RECESS_R))
    for hx, hy in power_holes():
        add.append(Part.makeCylinder(P_BOSS_OD / 2, P_Z_PCB_LO - PLATE_TOP + 0.01, V(hx, hy, PLATE_TOP - 0.01)))
        if END_WALL_IN - (hy + P_BOSS_OD / 2) < 1.0:
            # Too close to the end wall for a clean gap: tie the boss into it.
            add.append(box(hx - 1.5, hx + 1.5, hy, END_WALL_IN + 0.1, PLATE_TOP - 0.01, P_Z_PCB_LO))
        cut.append(Part.makeCylinder(P_PILOT / 2, P_PILOT_DEPTH + 1, V(hx, hy, P_Z_PCB_LO - P_PILOT_DEPTH)))

    add += speaker_holder()

    for s in pre_cut:
        desk = desk.cut(s)
    for s in add:
        desk = desk.fuse(s)
    for s in cut:
        desk = desk.cut(s)
    desk = desk.removeSplitter()
    return desk, (bx, by)


def board_dummy():
    """Envelope of the board as seated, for clearance checks."""
    parts = {}
    parts["pcb"] = box(X_USB, X_FAR, Y_C - PCB_W / 2, Y_C + PCB_W / 2, Z_PT, Z_PB)
    parts["usb"] = box(X_USB - USB_OVERHANG, X_USB - USB_OVERHANG + USB_LEN,
                       Y_C - USB_W / 2, Y_C + USB_W / 2, Z_PT - USB_H, Z_PT)
    bx = X_USB + BOOT_FROM_USB_EDGE
    for name, dy in (("boot", BOOT_FROM_AXIS), ("rst", -BOOT_FROM_AXIS)):
        parts[name] = box(bx - 1.5, bx + 1.5, Y_C + dy - 1.85, Y_C + dy + 1.85, Z_PT - 2.0, Z_PT)
    pin_x = [X_USB + 1.6 + 2.54 * k for k in range(8)]
    for side in (-1, 1):
        y = Y_C + side * 7.62
        parts[f"header{side}"] = box(pin_x[0] - 1.27, pin_x[-1] + 1.27, y - 1.27, y + 1.27, Z_PB, Z_PB + 2.5)
        parts[f"dupont{side}"] = box(pin_x[0] - 1.27, pin_x[-1] + 1.27, y - 1.27, y + 1.27, Z_PB + 2.5, Z_PB + 17.0)
        for k, x in enumerate(pin_x):
            parts[f"stub{side}_{k}"] = Part.makeCylinder(0.9, 2.0, V(x, y, Z_PT - 2.0))
    parts["antenna"] = box(X_FAR - 2.2, X_FAR - 0.2, Y_C - 3.25, Y_C + 3.25, Z_PT - 1.25, Z_PT)

    parts["pwr_pcb"] = box(P_X_EDGE, P_X_EDGE + P_PCB_L, P_Y_C - P_PCB_W / 2, P_Y_C + P_PCB_W / 2,
                           P_Z_PCB_LO, P_Z_PCB_LO + P_PCB_T)
    pwr_usb = box(P_X_FRONT, P_X_FRONT + P_USB_LEN, P_Y_C - USB_W / 2, P_Y_C + USB_W / 2,
                  P_Z_USB - USB_H / 2, P_Z_USB + USB_H / 2)
    long_edges = [e for e in pwr_usb.Edges if abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) > 1e-6]
    parts["pwr_usb"] = pwr_usb.makeFillet(1.2, long_edges)
    for i, (hx, hy) in enumerate(power_holes()):
        parts[f"pwr_screw_head{i}"] = Part.makeCylinder(2.75, 2.0, V(hx, hy, P_Z_PCB_LO + P_PCB_T))
    parts["speaker"] = speaker_body()
    return parts


def export(shape, name):
    for sub in ("step", "stl", "3mf"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    shape.exportStep(os.path.join(OUT, "step", name + ".step"))
    mesh = Mesh.Mesh(shape.tessellate(0.05))
    mesh.write(os.path.join(OUT, "stl", name + ".stl"))
    mesh.write(os.path.join(OUT, "3mf", name + ".3mf"))


if __name__ in ("__main__", "desk_supermini"):
    desk, boot = build()
    if not desk.isValid() or len(desk.Solids) != 1:
        raise SystemExit(f"bad result: valid={desk.isValid()} solids={len(desk.Solids)}")
    export(desk, "Desk")
    # Corner of the desk only, for a quick test print of the fit: no slatted end
    # wall, cut just above the clips.
    export(desk.common(box(-40, 7, -70.7, -44, -1, 18.6)), "DeskSuperMiniFitTest")
    # Same for the USB-C power breakout end, cut just above its PCB.
    export(desk.common(box(-40, -14, 44, 70.7, -1, P_Z_PCB_LO + P_PCB_T + 2)), "DeskUsbPowerFitTest")
    # Speaker holder on a square of desk top.
    export(desk.common(box(SPK_C[0] - 14, SPK_C[0] + 14, SPK_C[1] - 14, SPK_C[1] + 14, -1, 20)),
           "DeskSpeakerFitTest")
    print(f"BOOT pusher axis x={boot[0]:.2f} y={boot[1]:.2f}")
