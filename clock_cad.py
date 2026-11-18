"""
Vintage geared wall clock — 28BYJ-48 + ESP32-S3 — CadQuery
===========================================================

Movement layout (z = 0 at back face of back plate, +z towards viewer):

  z -19..0     28BYJ-48 body, behind the back plate (face screwed to plate)
  z  0..3      BACK PLATE (683ZZ bearing in a boss on its back side)
  z  3.5..8.5  motor pinion 15T (on motor shaft)  ->  centre wheel 30T (on arbor)
  z  3..13     4 pillars
  z 13..16     FRONT PLATE (683ZZ bearing in a boss on its inner side)
  z 16.5..21.5 cannon pinion 15T  ->  minute wheel 45T   (3:1)
  z 21.5..26.5 minute pinion 12T  ->  hour wheel 48T     (4:1)   => 12:1
  z 30..33     DIAL (bosses reach back to the front plate)
  z 33.5..     hour hand on 5 mm brass pipe, minute hand on 4 mm brass cannon tube

Drive: motor 15T -> centre wheel 30T = 2 motor turns per hour.
Gears: module 1, 20 deg pressure angle (same standard as the earlier parts set).

Run:  python clock_cad.py      -> out/*.stl, out/clock_assembly.step, dial PNG/PDF
"""
import math, os
import cadquery as cq

OUT = "out"
FONT = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"   # any serif TTF; None = default
if FONT and not os.path.exists(FONT):
    FONT = None

# ---------------- general fits ----------------
FIT        = 0.15     # double-D shaft clearance
SHAFT_D, SHAFT_FLAT = 5.0, 3.0
ARBOR_D    = 3.0      # steel/brass rod
CANNON_D   = 4.0      # brass tube 4 OD / ~3.1 ID  (glued on arbor)
PIPE_D     = 5.0      # brass tube 5 OD / ~4.1 ID  (hour pipe, turns on cannon)
BRG_OD, BRG_W = 7.0, 3.0      # 683ZZ
M3_CLR, M3_TAP = 3.3, 2.5
MAG_D, MAG_H = 3.1, 2.1       # 3 x 2 mm neodymium disc pocket

# ---------------- gearing ----------------
MODULE, PRESSURE, BACKLASH = 1.0, 20.0, 0.12
Z_MOTOR, Z_CENTRE = 15, 30
Z_CANNON, Z_MINWHEEL = 15, 45
Z_MINPINION, Z_HOUR = 12, 48
GEAR_T = 5.0

def cd(z1, z2):
    return MODULE * (z1 + z2) / 2

MOTOR_XY  = (0.0, -cd(Z_MOTOR, Z_CENTRE))          # (0, -22.5)
STUD_XY   = (cd(Z_CANNON, Z_MINWHEEL), 0.0)        # (30, 0)
assert abs(cd(Z_CANNON, Z_MINWHEEL) - cd(Z_MINPINION, Z_HOUR)) < 1e-9
MOTOR_BODY = (0.0, MOTOR_XY[1] - 8.0)              # shaft is 8 mm off body centre
MOTOR_EARS = [(MOTOR_BODY[0] + s * 17.5, MOTOR_BODY[1]) for s in (-1, 1)]

PILLARS   = [(-30, 20), (-30, -20), (22, -35), (20, 35)]
MIN_SENSOR_XY  = (0.0, 10.0)      # on back plate, under centre wheel
HOUR_SENSOR_XY = (-18.0, 0.0)     # on raised pad on front plate, under hour wheel

# ---------------- z stack ----------------
BP_T, PILLAR_H, FP_T = 3.0, 10.0, 3.0
Z_BP0, Z_BP1 = 0.0, BP_T
Z_FP0 = Z_BP1 + PILLAR_H
Z_FP1 = Z_FP0 + FP_T
Z_DRIVE  = Z_BP1 + 0.5            # motor pinion / centre wheel layer
Z_MW     = Z_FP1 + 0.5            # cannon / minute wheel layer
Z_HW     = Z_MW + GEAR_T          # minute pinion / hour wheel layer
DIAL_T   = 3.0
Z_DIAL   = Z_HW + GEAR_T + 3.5    # clearance for M3 nut on the stud
Z_HH     = Z_DIAL + DIAL_T + 0.5  # hour hand
HAND_T, HUB_H = 1.6, 3.0
Z_MH     = Z_HH + HUB_H + 1.0     # minute hand

DIAL_R = 90.0


# =====================================================================
# helpers
# =====================================================================
def involute_outline(z, m=MODULE, pa_deg=PRESSURE, backlash=BACKLASH, steps=10):
    pa = math.radians(pa_deg)
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    rb = rp * math.cos(pa)
    inv = lambda a: math.tan(a) - a
    half = math.pi / (2 * z) - backlash / (2 * rp)
    r0 = max(rb, rf)
    fa = lambda r: inv(pa) - inv(math.acos(min(1.0, rb / r)))
    pts, pitch = [], 2 * math.pi / z
    for i in range(z):
        c = i * pitch
        lower = ([(rf, c - half - fa(rb))] if rf < rb else []) + \
                [(r0 + (ra - r0) * k / steps, c - half - fa(r0 + (ra - r0) * k / steps))
                 for k in range(steps + 1)]
        upper = [(r, 2 * c - a) for r, a in reversed(lower)]
        tip = [(ra, lower[-1][1] + (upper[0][1] - lower[-1][1]) * t / 3) for t in (1, 2)]
        seq = lower + tip + upper
        nxt = (i + 1) * pitch - half - fa(rb if rf < rb else rf)
        root = [(rf, seq[-1][1] + (nxt - seq[-1][1]) * t / 4) for t in (1, 2, 3)]
        pts += [(r * math.cos(a), r * math.sin(a)) for r, a in seq + root]
    return pts


def gear_blank(z, t=GEAR_T):
    return cq.Workplane("XY").polyline(involute_outline(z)).close().extrude(t)


def cyl(r, h, xy=(0, 0), z0=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(*xy).circle(r).extrude(h)


def d_bore(h, z0=0.0):
    d, f = SHAFT_D + FIT, SHAFT_FLAT + FIT
    return (cyl(d / 2, h + 1, z0=z0 - 0.5)
            .intersect(cq.Workplane("XY").workplane(offset=z0 - 0.5).rect(f, d + 1).extrude(h + 1)))


def crossings(g, r_in, r_out, n, spoke_w, t, skip_angle=None):
    """Classic clock-wheel spokes: cut n windows between r_in and r_out."""
    for k in range(n):
        a0 = 360 / n * k
        a1 = a0 + 360 / n
        mid = (a0 + a1) / 2
        hw = math.degrees((spoke_w / 2) / r_in)
        hwo = math.degrees((spoke_w / 2) / r_out)
        P = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
        win = (cq.Workplane("XY").workplane(offset=-0.5)
               .moveTo(*P(r_in, a0 + hw)).lineTo(*P(r_out, a0 + hwo))
               .threePointArc(P(r_out, mid), P(r_out, a1 - hwo))
               .lineTo(*P(r_in, a1 - hw))
               .threePointArc(P(r_in, mid), P(r_in, a0 + hw)).close()
               .extrude(t + 1))
        g = g.cut(win)
    return g


def bar(p1, p2, w):
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return (cq.Workplane("XY").center((x1 + x2) / 2, (y1 + y2) / 2)
            .transformed(rotate=(0, 0, ang)).rect(L, w).extrude(1))


def skeleton_plate(nodes, links, t, bar_w=8.0):
    """nodes: {name: ((x,y), r)}; links: [(a,b)] -> plate of discs + bars."""
    p = None
    for (xy, r) in nodes.values():
        s = cyl(r, 1, xy)
        p = s if p is None else p.union(s)
    for a, b in links:
        p = p.union(bar(nodes[a][0], nodes[b][0], bar_w))
    # scale thickness by re-extruding the outline face
    return cq.Workplane("XY").add(p.faces("<Z").vals()[0]).wires().toPending().extrude(t)


def sensor_pocket(xy, z_top, outward_deg):
    """Pocket for a flat A3144 (4.1 x 3 x 1.5) face-up at z_top, legs bent through a slot."""
    a = outward_deg
    pocket = (cq.Workplane("XY").workplane(offset=z_top - 1.6).center(*xy)
              .transformed(rotate=(0, 0, a)).rect(3.4, 4.5).extrude(2))
    ox, oy = (xy[0] + 2.2 * math.cos(math.radians(a)), xy[1] + 2.2 * math.sin(math.radians(a)))
    slot = (cq.Workplane("XY").workplane(offset=z_top - 30).center(ox, oy)
            .transformed(rotate=(0, 0, a)).rect(1.4, 4.5).extrude(31))
    return pocket.union(slot)


# =====================================================================
# wheels
# =====================================================================
def motor_pinion():
    g = gear_blank(Z_MOTOR)
    return g.cut(d_bore(GEAR_T))


def centre_wheel():
    g = gear_blank(Z_CENTRE).union(cyl(4.5, 1.5, z0=GEAR_T))      # front hub
    g = g.cut(cyl(ARBOR_D / 2, 10, z0=-1))
    # magnet pocket on back face at r = 10 (angle 90 deg = 'twelve')
    return g.cut(cyl(MAG_D / 2, MAG_H, (0, 10), z0=0))


def cannon_pinion():
    g = gear_blank(Z_CANNON)
    return g.cut(cyl(CANNON_D / 2 + 0.02, 10, z0=-1))


def minute_wheel():
    """45T wheel + 12T pinion as one part, turns on an M3 screw stud."""
    w = gear_blank(Z_MINWHEEL)
    w = crossings(w, 7, 18, 5, 3.5, GEAR_T)
    p = gear_blank(Z_MINPINION).translate((0, 0, GEAR_T))
    w = w.union(p).union(cyl(5, GEAR_T, z0=0))                     # hub through crossings
    return w.cut(cyl(M3_CLR / 2, 20, z0=-1))


def hour_wheel():
    w = gear_blank(Z_HOUR)
    w = crossings(w, 6, 14, 5, 3.5, GEAR_T)
    w = w.union(cyl(5.5, GEAR_T))
    w = w.cut(cyl(PIPE_D / 2 + 0.02, 20, z0=-1))
    return w.cut(cyl(MAG_D / 2, MAG_H, (-18, 0), z0=0))            # magnet, back face


# =====================================================================
# plates
# =====================================================================
def back_plate():
    nodes = {
        "c":  ((0, 0), 16),
        "m":  (MOTOR_XY, 10),
        "e1": (MOTOR_EARS[0], 5.5), "e2": (MOTOR_EARS[1], 5.5),
        "p1": (PILLARS[0], 5.5), "p2": (PILLARS[1], 5.5),
        "p3": (PILLARS[2], 5.5), "p4": (PILLARS[3], 5.5),
        "top": ((0, 38), 9), "f1": ((-25, -50), 5.5), "f2": ((25, -50), 5.5),
    }
    links = [("c", "p1"), ("c", "p2"), ("c", "p3"), ("c", "p4"), ("c", "m"),
             ("m", "e1"), ("m", "e2"), ("e1", "f1"), ("e2", "f2"), ("e1", "p2"),
             ("e2", "p3"), ("p4", "top"), ("p1", "top"), ("c", "top")]
    p = skeleton_plate(nodes, links, BP_T)
    # bearing boss on back side
    p = p.union(cyl(6.5, 2.5, z0=-2.5))
    p = p.cut(cyl(BRG_OD / 2 + 0.05, BRG_W, z0=-2.5)).cut(cyl(2.2, 10, z0=-5))
    # motor: boss hole + ear holes
    p = p.cut(cyl(5.0, 10, MOTOR_XY, -1))
    for e in MOTOR_EARS:
        p = p.cut(cyl(4.2 / 2, 10, e, -1))
    for xy in PILLARS:
        p = p.cut(cyl(M3_CLR / 2, 10, xy, -1)).cut(cyl(3.1, 1.6, xy, -0.01))  # head recess
    p = p.cut(sensor_pocket(MIN_SENSOR_XY, Z_BP1, 90))
    # wall feet (clear the motor body, 22 mm) with keyhole at top
    for xy in [(0, 38), (-25, -50), (25, -50)]:
        p = p.union(cyl(5.5 if xy[1] < 0 else 9, 22, xy, z0=-22))
    # keyhole: head enters at y=34, slides to y=40 behind a 2 mm lip
    p = p.cut(cyl(4.4, 2.6, (0, 34), z0=-22.5))                       # entry through lip
    p = p.cut(cq.Workplane("XY").workplane(offset=-22.5).center(0, 37).rect(4.4, 6).extrude(2.6))
    p = p.cut(cyl(2.2, 2.6, (0, 40), z0=-22.5))
    p = p.cut(cyl(4.4, 4, (0, 34), z0=-20))                           # head cavity
    p = p.cut(cq.Workplane("XY").workplane(offset=-20).center(0, 37).rect(8.8, 6).extrude(4))
    p = p.cut(cyl(4.4, 4, (0, 40), z0=-20))
    return p


def front_plate():
    nodes = {
        "c": ((0, 0), 12), "s": (STUD_XY, 6.5), "h": (HOUR_SENSOR_XY, 7),
        "p1": (PILLARS[0], 5.5), "p2": (PILLARS[1], 5.5),
        "p3": (PILLARS[2], 5.5), "p4": (PILLARS[3], 5.5),
    }
    links = [("c", "p1"), ("c", "p2"), ("c", "p3"), ("c", "p4"), ("c", "s"), ("c", "h")]
    p = skeleton_plate(nodes, links, FP_T).translate((0, 0, Z_FP0))
    # bearing boss on inner side (behind the plate)
    p = p.union(cyl(6.5, 2.5, z0=Z_FP0 - 2.5))
    p = p.cut(cyl(BRG_OD / 2 + 0.05, BRG_W, z0=Z_FP0 - 2.5)).cut(cyl(2.2, 10, z0=Z_FP0))
    p = p.cut(cyl(M3_CLR / 2, 10, STUD_XY, Z_FP0 - 1))
    for xy in PILLARS:
        p = p.cut(cyl(M3_CLR / 2, 10, xy, Z_FP0 - 1))
    # raised pad for hour sensor so it sits 1.5 mm under the hour wheel
    pad_top = Z_HW - 1.5
    p = p.union(cq.Workplane("XY").workplane(offset=Z_FP1).center(*HOUR_SENSOR_XY)
                .rect(7, 8).extrude(pad_top - Z_FP1))
    return p.cut(sensor_pocket(HOUR_SENSOR_XY, pad_top, 180))


def pillar():
    return cyl(4, PILLAR_H).cut(cyl(M3_CLR / 2, PILLAR_H + 2, z0=-1))


# =====================================================================
# dial
# =====================================================================
ROMAN = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
ENGRAVE = 0.8
R_TRACK_O, R_TRACK_I = 82.0, 77.0
R_NUM, NUM_H = 66.0, 12.0
R_INNER = 56.0


def dial_marks():
    """Solid of everything engraved into the dial front (also the 2-colour inlay)."""
    z = DIAL_T - ENGRAVE
    def ring(r, w):
        return (cq.Workplane("XY").workplane(offset=z).circle(r + w / 2)
                .circle(r - w / 2).extrude(ENGRAVE + 0.01))
    m = ring(R_TRACK_O, 0.8).union(ring(R_TRACK_I, 0.8)).union(ring(R_INNER, 0.6))
    m = m.union(ring(R_TRACK_O + 3.0, 0.5))
    for i in range(60):
        a = 90 - i * 6
        big = i % 5 == 0
        L = R_TRACK_O - R_TRACK_I
        w = 1.6 if big else 0.6
        t = (cq.Workplane("XY").workplane(offset=z)
             .center((R_TRACK_I + L / 2), 0).rect(L, w).extrude(ENGRAVE + 0.01)
             .rotate((0, 0, 0), (0, 0, 1), a))
        m = m.union(t)
        if big:   # small diamond pip outside the track
            d = (cq.Workplane("XY").workplane(offset=z)
                 .polyline([(R_TRACK_O + 1.2, 0), (R_TRACK_O + 3, 1.0),
                            (R_TRACK_O + 4.8, 0), (R_TRACK_O + 3, -1.0)]).close()
                 .extrude(ENGRAVE + 0.01).rotate((0, 0, 0), (0, 0, 1), a))
            m = m.union(d)
    for h, txt in enumerate(ROMAN):
        a = 90 - h * 30
        kw = dict(combine=False, halign="center", valign="center")
        if FONT:
            kw["fontPath"] = FONT
        t = (cq.Workplane("XY").workplane(offset=z)
             .text(txt, NUM_H, ENGRAVE + 0.01, **kw)
             .rotate((0, 0, 0), (0, 0, 1), a - 90)
             .translate((R_NUM * math.cos(math.radians(a)), R_NUM * math.sin(math.radians(a)), 0)))
        m = m.union(t)
    return m


def dial(engrave=True):
    d = cyl(DIAL_R, DIAL_T)
    # short skirt behind the dial hides the movement (face stays flat: prints face-down)
    d = d.union(cq.Workplane("XY").workplane(offset=-12).circle(DIAL_R).circle(DIAL_R - 2).extrude(12))
    d = d.cut(cyl(PIPE_D / 2 + 0.6, 10, z0=-1))
    if engrave:
        d = d.cut(dial_marks())
    # mounting bosses back to the front plate (self-tap M3 from behind)
    boss_h = Z_DIAL - Z_FP1
    for xy in PILLARS:
        d = d.union(cyl(4.5, boss_h, xy, z0=-boss_h))
        d = d.cut(cyl(M3_TAP / 2, 10, xy, z0=-boss_h - 0.1))
        d = d.cut(cyl(3.4, 2.7, xy, z0=-boss_h - 0.1))     # clears the M3 nut that clamps the movement
    return d


# =====================================================================
# hands (spade hour, slim pointed minute with tail)
# =====================================================================
def hand_profile(pts):
    """Mirror a right-half outline (x>=0, along +y) into a closed hand."""
    full = pts + [(-x, y) for x, y in reversed(pts) if x > 0]
    return cq.Workplane("XY").polyline(full).close().extrude(HAND_T)


def hour_hand():
    L = 50
    half = [(0, -8), (2.2, -7), (1.4, 4), (1.2, L - 22),
            (5.5, L - 16), (6.5, L - 11), (4.5, L - 7), (1.2, L - 5), (0, L)]
    h = hand_profile(half)
    h = h.cut(cq.Workplane("XY").center(0, L - 12).ellipse(1.6, 3.0).extrude(5).translate((0, 0, -1)))
    h = h.union(cyl(5.2, HUB_H)).union(cyl(4.0, 1.0, (0, -8)))
    return h.cut(cyl(PIPE_D / 2, 10, z0=-1))


def minute_hand():
    L = 78
    half = [(0, -18), (3.5, -16), (2.0, -9), (1.4, 5), (1.0, L - 16),
            (3.0, L - 11), (1.0, L - 6), (0.5, L - 2), (0, L)]
    h = hand_profile(half)
    h = h.union(cyl(4.6, HUB_H)).union(cyl(4.5, HAND_T, (0, -16)))   # tail counterweight disc
    return h.cut(cyl(CANNON_D / 2, 10, z0=-1))


# =====================================================================
# build, check, export
# =====================================================================
def mesh_rot(r_driver, z_driver, z_driven, dir_deg):
    """Rotation for a driven gear so it meshes with a driver whose rotation is r_driver.
    dir_deg: direction from driver centre to driven centre."""
    pd, pn = 360 / z_driver, 360 / z_driven
    r0 = dir_deg                       # driver tooth pointing at driven
    w0 = dir_deg + 180 + pn / 2        # driven gap pointing back at driver
    return w0 - (r_driver - r0) * z_driver / z_driven


def place(part, xy=(0, 0), z=0.0, rot=0.0):
    return part.rotate((0, 0, 0), (0, 0, 1), rot).translate((xy[0], xy[1], z))


def build():
    P = {}
    P["back_plate"]    = back_plate()
    P["front_plate"]   = front_plate()
    P["pillar"]        = pillar()
    P["motor_pinion"]  = motor_pinion()
    P["centre_wheel"]  = centre_wheel()
    P["cannon_pinion"] = cannon_pinion()
    P["minute_wheel"]  = minute_wheel()
    P["hour_wheel"]    = hour_wheel()
    P["dial"]          = dial()
    P["dial_plain"]    = dial(engrave=False)
    P["dial_inlay_2colour"] = dial_marks()
    P["hour_hand"]     = hour_hand()
    P["minute_hand"]   = minute_hand()
    return P


def assemble(P, minute_deg=0.0):
    """Clock at 10:10-ish for the render. Returns {name: placed solid}."""
    A = {}
    A["back_plate"]  = P["back_plate"]
    A["front_plate"] = P["front_plate"]
    for i, xy in enumerate(PILLARS):
        A[f"pillar{i}"] = place(P["pillar"], xy, Z_BP1)
    # drive: motor pinion is driver, direction to centre = +90
    r_mp = 0.0
    A["motor_pinion"] = place(P["motor_pinion"], MOTOR_XY, Z_DRIVE, r_mp)
    r_cw = mesh_rot(r_mp, Z_MOTOR, Z_CENTRE, 90)
    A["centre_wheel"] = place(P["centre_wheel"], (0, 0), Z_DRIVE, r_cw)
    # motion works: cannon pinion (driver) -> minute wheel at +x
    r_cp = 0.0
    A["cannon_pinion"] = place(P["cannon_pinion"], (0, 0), Z_MW, r_cp)
    r_mw = mesh_rot(r_cp, Z_CANNON, Z_MINWHEEL, 0)
    A["minute_wheel"] = place(P["minute_wheel"], STUD_XY, Z_MW, r_mw)
    r_hw = mesh_rot(r_mw, Z_MINPINION, Z_HOUR, 180)
    A["hour_wheel"] = place(P["hour_wheel"], (0, 0), Z_HW, r_hw)
    A["dial"] = place(P["dial"], (0, 0), Z_DIAL)
    A["hour_hand"] = place(P["hour_hand"], (0, 0), Z_HH, -305)     # ~10 o'clock
    A["minute_hand"] = place(P["minute_hand"], (0, 0), Z_MH, -60)  # 10 past
    return A


def interference(A, skip=()):
    names = list(A)
    hits = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if (a, b) in skip or (b, a) in skip:
                continue
            ba, bb = A[a].val().BoundingBox(), A[b].val().BoundingBox()
            if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or
                    bb.ymax < ba.ymin or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
                continue
            v = A[a].intersect(A[b]).val().Volume()
            if v > 0.05:
                hits.append((a, b, round(v, 2)))
    return hits


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    P = build()
    for n, p in P.items():
        part = p
        if n in ("dial", "dial_plain"):                       # print face-down
            part = p.rotate((0, 0, 0), (1, 0, 0), 180)
        cq.exporters.export(part, f"{OUT}/{n}.stl")
    A = assemble(P)
    asm = cq.Assembly()
    colours = {"dial": "ivory", "hour_hand": "black", "minute_hand": "black",
               "back_plate": "goldenrod", "front_plate": "goldenrod"}
    for n, s in A.items():
        asm.add(s, name=n, color=cq.Color(colours.get(n, "darkgoldenrod")))
    asm.save(f"{OUT}/clock_assembly.step")
    for n, s in A.items():
        cq.exporters.export(s, f"{OUT}/_asm_{n}.stl")
    # pillars are meant to touch plates; dial bosses touch front plate
    skip = {(f"pillar{i}", p) for i in range(4) for p in ("back_plate", "front_plate")}
    skip |= {("dial", "front_plate")}
    print("interference:", interference(A, skip) or "none")
    print("Z: back plate 0..3, front plate", Z_FP0, "..", Z_FP1, " dial", Z_DIAL,
          " hour hand", Z_HH, " minute hand", Z_MH)
    print("tube/rod lengths (mm): arbor 3mm ~", round(Z_MH - 4 - (-2.5)),
          " cannon 4mm ~", round(Z_MH + HUB_H + 0.5 - Z_MW),
          " hour pipe 5mm ~", round(Z_HH + HUB_H + 0.5 - Z_HW))
