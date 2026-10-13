"""Generate the OLED business-card PCB (ISO/IEC 7810 ID-1: 85.6 x 54 mm) for KiCad.

Parts: Seeed XIAO ESP32-S3 (castellated pads, USB-C = program + LiPo charge),
0.91" 128x32 I2C SSD1306 OLED module (4-pin header), 6mm tactile button.
Run:  python gen_card.py   ->  oled_card.kicad_pcb
"""
import uuid

W, H, R = 85.6, 54.0, 3.18          # credit-card size, corner radius
NOTCH_DEPTH, NOTCH_Y0, NOTCH_Y1 = 2.0, 20.5, 33.5   # USB-C plug relief
NETS = ["", "GND", "3V3", "SDA", "SCL", "BTN"]
N = {n: i for i, n in enumerate(NETS)}
TW = 0.25                            # track width

out = []
def uid(): return str(uuid.uuid4())
def seg(pts, net, layer="F.Cu"):
    for (a, b), (c, d) in zip(pts, pts[1:]):
        out.append(f'(segment (start {a:.3f} {b:.3f}) (end {c:.3f} {d:.3f}) '
                   f'(width {TW}) (layer "{layer}") (net {N[net]}) (uuid "{uid()}"))')
def via(x, y, net):
    out.append(f'(via (at {x:.3f} {y:.3f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
               f'(net {N[net]}) (uuid "{uid()}"))')
def text(s, x, y, layer="F.SilkS", size=1.2, mirror=False):
    m = " (justify mirror)" if mirror else ""
    out.append(f'(gr_text "{s}" (at {x} {y}) (layer "{layer}") (uuid "{uid()}") '
               f'(effects (font (size {size} {size}) (thickness {size/8:.2f})){m}))')
def line(a, b, layer, w=0.12):
    out.append(f'(gr_line (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) '
               f'(stroke (width {w}) (type default)) (layer "{layer}") (uuid "{uid()}"))')
def rect(x0, y0, x1, y1, layer):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for a, b in zip(pts, pts[1:]): line(a, b, layer)
def arc(s, m, e):
    out.append(f'(gr_arc (start {s[0]:.3f} {s[1]:.3f}) (mid {m[0]:.3f} {m[1]:.3f}) '
               f'(end {e[0]:.3f} {e[1]:.3f}) (stroke (width 0.1) (type default)) '
               f'(layer "Edge.Cuts") (uuid "{uid()}"))')

def footprint(ref, value, pads):
    """Footprint at origin; pads carry absolute board coordinates."""
    body = "\n    ".join(pads)
    out.append(f'''(footprint "{ref}_{value}" (layer "F.Cu") (uuid "{uid()}") (at 0 0)
    (property "Reference" "{ref}" (at 0 0) (layer "F.SilkS") (hide yes) (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{value}" (at 0 0) (layer "F.Fab") (hide yes) (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))
    {body}
  )''')

def smd(num, x, y, w, h, net):
    n = f' (net {N[net]} "{net}")' if net else ""
    return (f'(pad "{num}" smd rect (at {x:.3f} {y:.3f}) (size {w} {h}) '
            f'(layers "F.Cu" "F.Mask" "F.Paste"){n} (uuid "{uid()}"))')
def tht(num, x, y, d, drill, net):
    n = f' (net {N[net]} "{net}")' if net else ""
    return (f'(pad "{num}" thru_hole circle (at {x:.3f} {y:.3f}) (size {d} {d}) (drill {drill}) '
            f'(layers "*.Cu" "*.Mask"){n} (uuid "{uid()}"))')

# ---------------------------------------------------------------- outline
def outline():
    P = lambda a, b: line(a, b, "Edge.Cuts", 0.1)
    k = R * (1 - 0.70710678)
    P((R, 0), (W - R, 0));           arc((W - R, 0), (W - k, k), (W, R))
    P((W, R), (W, H - R));           arc((W, H - R), (W - k, H - k), (W - R, H))
    P((W - R, H), (R, H));           arc((R, H), (k, H - k), (0, H - R))
    P((0, H - R), (0, NOTCH_Y1));    P((0, NOTCH_Y1), (NOTCH_DEPTH, NOTCH_Y1))
    P((NOTCH_DEPTH, NOTCH_Y1), (NOTCH_DEPTH, NOTCH_Y0)); P((NOTCH_DEPTH, NOTCH_Y0), (0, NOTCH_Y0))
    P((0, NOTCH_Y0), (0, R));        arc((0, R), (k, k), (R, 0))

# ---------------------------------------------------------------- XIAO ESP32-S3
# Module is 21 x 17.8 mm, USB-C end pointing -X (into the edge notch).
CY = H / 2
USB_X = NOTCH_DEPTH + 0.2           # module PCB edge
CX = USB_X + 10.5
# Local XIAO frame: USB up (-y). Left col pins 1..7 = D0..D6, right col pins 8..14 = D7..5V (bottom->top)
LEFT = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]
RIGHT = ["D7", "D8", "D9", "D10", "3V3", "GND", "5V"]
XIAO_NET = {"D1": "BTN", "D4": "SDA", "D5": "SCL", "3V3": "3V3", "GND": "GND"}
pos = {}   # name -> (x, y) on board after rotating USB to the left
pads = []
for i, nme in enumerate(LEFT):
    ly = -7.62 + 2.54 * i; lx = -8.89
    pos[nme] = (CX + ly, CY - lx)
for k, nme in enumerate(RIGHT):
    ly = 7.62 - 2.54 * k; lx = 8.89
    pos[nme] = (CX + ly, CY - lx)
for idx, nme in enumerate(LEFT + RIGHT, 1):
    x, y = pos[nme]
    pads.append(smd(idx, x, y, 1.4, 3.0, XIAO_NET.get(nme)))
footprint("U1", "XIAO_ESP32S3", pads)

# ---------------------------------------------------------------- OLED header (GND VCC SCL SDA)
HX = 30.0
OLED = [("GND", "GND"), ("VCC", "3V3"), ("SCL", "SCL"), ("SDA", "SDA")]
oy = {}
pads = []
for i, (nm, net) in enumerate(OLED):
    y = CY - 3.81 + 2.54 * i
    oy[net] = y
    pads.append(tht(i + 1, HX, y, 1.7, 1.0, net))
footprint("J1", "OLED_0.91_I2C", pads)

# ---------------------------------------------------------------- Tactile button 6x6 THT
BX, BY = 30.0, 47.0
pads = [tht(1, BX - 3.25, BY - 2.25, 1.8, 1.0, "GND"), tht(2, BX - 3.25, BY + 2.25, 1.8, 1.0, "GND"),
        tht(3, BX + 3.25, BY - 2.25, 1.8, 1.0, "BTN"), tht(4, BX + 3.25, BY + 2.25, 1.8, 1.0, "BTN")]
footprint("SW1", "TACT_6x6", pads)

# ---------------------------------------------------------------- routing (F.Cu)
g, v = pos["GND"], pos["3V3"]
seg([g, (g[0], 14.0), (28.5, 14.0), (28.5, oy["GND"]), (HX, oy["GND"])], "GND")
seg([v, (v[0], 15.5), (27.0, 15.5), (27.0, oy["3V3"]), (HX, oy["3V3"])], "3V3")
d, c = pos["D4"], pos["D5"]
seg([d, (d[0], 40.0), (28.5, 40.0), (28.5, oy["SDA"]), (HX, oy["SDA"])], "SDA")
seg([c, (c[0], 38.5), (27.0, 38.5), (27.0, oy["SCL"]), (HX, oy["SCL"])], "SCL")
b = pos["D1"]
seg([b, (b[0], 51.5), (BX + 3.25, 51.5), (BX + 3.25, BY + 2.25), (BX + 3.25, BY - 2.25)], "BTN")
seg([(BX - 3.25, BY - 2.25), (BX - 3.25, BY + 2.25)], "GND", "B.Cu")
# ground return for the button on the back copper
via(28.5, 18.0, "GND")
seg([(28.5, 18.0), (24.0, 18.0), (24.0, BY - 2.25), (BX - 3.25, BY - 2.25)], "GND", "B.Cu")
# keep a GND pour on the back (fills when you press B in KiCad); battery sits on it
out.append(f'(zone (net {N["GND"]}) (net_name "GND") (layer "B.Cu") (uuid "{uid()}") (hatch edge 0.5) '
           f'(connect_pads (clearance 0.3)) (min_thickness 0.2) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.4)) '
           f'(polygon (pts (xy 3 3) (xy {W-3} 3) (xy {W-3} {H-3}) (xy 3 {H-3}))))')

# ---------------------------------------------------------------- silk / graphics
outline()
rect(USB_X, CY - 8.9, USB_X + 21, CY + 8.9, "F.SilkS")           # XIAO outline
text("XIAO ESP32-S3", USB_X + 10.5, CY - 11.5, size=0.9)
text("USB-C: PROGRAM + CHARGE", 14.5, 4.5, size=0.9)
rect(HX - 1.5, CY - 6.0, HX + 36.5, CY + 6.0, "F.SilkS")          # OLED module footprint
text("YOUR NAME", 62, 8.0, size=2.0)
text("your title - you@email.com", 62, 12.0, size=1.0)
text("BTN", BX, BY - 5.8, size=0.9)
text("LiPo 3.7V <=30x25x4mm", 52, 40, "B.SilkS", 1.0, mirror=True)
rect(34, 20, 70, 46, "B.SilkS")                                  # battery area (back)
text("BAT+/BAT- -> XIAO back pads", 52, 17, "B.SilkS", 0.9, mirror=True)

hdr = f'''(kicad_pcb (version 20240108) (generator "gen_card") (generator_version "1.0")
  (general (thickness 0.8) (legacy_teardrops no))
  (paper "A4")
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))
  (setup (pad_to_mask_clearance 0)
    (stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "core") (thickness 0.69) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG") (dielectric_constraints no)))
  {" ".join(f'(net {i} "{n}")' for i, n in enumerate(NETS))}
'''
with open("oled_card.kicad_pcb", "w") as f:
    f.write(hdr + "\n".join(out) + "\n)\n")
print("wrote oled_card.kicad_pcb")
