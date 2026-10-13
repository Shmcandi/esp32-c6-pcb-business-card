"""All-in-one OLED business card: ESP32-S3 + USB-C + LiPo charger + LDO on one 85.6x54 mm PCB.
Designed for turnkey assembly (JLCPCB-style PCBA): the user solders nothing.
  - ESP32-S3-WROOM-1 module (native USB: program/debug straight over USB-C, no UART chip needed)
  - USB-C receptacle, MCP73831 LiPo charger, AP2112K-3.3 LDO
  - EN / BOOT / USER buttons, charge LED
  - JST-PH battery plug, 4-pin socket for a plug-in 0.91" I2C OLED module

Run with KiCad's python:
  "C:/Program Files/KiCad/10.0/bin/python.exe" aio_card.py
"""
import math
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "aio_card.kicad_pcb")
DSN = os.path.join(HERE, "aio_card.dsn")
SES = os.path.join(HERE, "aio_card.ses")
JAR = os.path.join(os.path.dirname(HERE), "tools", "freerouting-1.9.0.jar")
LIB = "C:/Program Files/KiCad/10.0/share/kicad/footprints/"

W, H, RC = 85.6, 54.0, 3.18
KEEPOUT_X = 78.9           # antenna keepout starts here (module antenna points to +x)

FM = pcbnew.FromMM
def v2i(x, y): return pcbnew.VECTOR2I(FM(x), FM(y))
def ang(a): return pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T)

FP = {
    "esp": ("RF_Module", "ESP32-S3-WROOM-1"),
    "usb": ("Connector_USB", "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"),
    "jst": ("Connector_JST", "JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal"),
    "sw": ("Button_Switch_SMD", "SW_SPST_PTS810"),
    "sot5": ("Package_TO_SOT_SMD", "SOT-23-5"),
    "sock": ("Connector_PinHeader_2.54mm", "PinHeader_1x06_P2.54mm_Vertical"),
    "r": ("Resistor_SMD", "R_0603_1608Metric"),
    "c6": ("Capacitor_SMD", "C_0603_1608Metric"),
    "c8": ("Capacitor_SMD", "C_0805_2012Metric"),
    "led": ("LED_SMD", "LED_0603_1608Metric"),
}

NETS = ["GND", "VBUS", "VBAT", "3V3", "USB_DP", "USB_DN", "CC1", "CC2", "EN", "IO0",
        "SCK", "MOSI", "RES", "DC", "BTN", "STAT", "PROG", "LEDA"]

# ref, kind, value, x, y, rot, {pad: net}
PARTS = [
    ("U1", "esp", "ESP32-S3-WROOM-1-N8", 73.05, 27.0, -90,
        {"1": "GND", "40": "GND", "41": "GND", "2": "3V3", "3": "EN", "27": "IO0",
         "13": "USB_DN", "14": "USB_DP", "17": "BTN", "18": "SCK", "19": "MOSI", "20": "RES", "21": "DC"}),
    ("J1", "usb", "USB-C (USB4105)", 4.2, 27.0, -90,
        {"A1": "GND", "B12": "GND", "A12": "GND", "B1": "GND", "SH": "GND",
         "A4": "VBUS", "B9": "VBUS", "A9": "VBUS", "B4": "VBUS",
         "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
         "A7": "USB_DN", "B7": "USB_DN"}),
    ("R1", "r", "5.1k", 12.0, 22.0, 90, {"1": "CC1", "2": "GND"}),
    ("R2", "r", "5.1k", 12.0, 32.0, 90, {"1": "CC2", "2": "GND"}),
    ("C1", "c8", "4.7uF", 12.5, 13.0, 90, {"1": "VBUS", "2": "GND"}),
    ("U2", "sot5", "MCP73831T-2ACI/OT", 20.0, 10.0, 0,
        {"1": "STAT", "2": "GND", "3": "VBAT", "4": "VBUS", "5": "PROG"}),
    ("R3", "r", "3.3k", 20.0, 16.0, 0, {"1": "PROG", "2": "GND"}),
    ("C2", "c8", "4.7uF", 27.5, 10.0, 90, {"1": "VBAT", "2": "GND"}),
    ("R6", "r", "1k", 33.0, 7.0, 0, {"1": "VBUS", "2": "LEDA"}),
    ("D1", "led", "CHG", 38.0, 7.0, 0, {"1": "STAT", "2": "LEDA"}),
    ("J2", "jst", "BATT JST-PH", 48.0, 6.5, 0, {"1": "VBAT", "2": "GND", "MP": "GND"}),
    ("U3", "sot5", "AP2112K-3.3", 24.0, 44.0, 0,
        {"1": "VBAT", "3": "VBAT", "2": "GND", "5": "3V3"}),
    ("C3", "c8", "10uF", 17.5, 44.0, 90, {"1": "VBAT", "2": "GND"}),
    ("C4", "c8", "10uF", 30.5, 44.0, 90, {"1": "3V3", "2": "GND"}),
    ("J3", "sock", "OLED 6-pin SPI", 18.0, 19.38, 0,
        {"1": "GND", "2": "3V3", "3": "SCK", "4": "MOSI", "5": "RES", "6": "DC"}),
    ("SW1", "sw", "EN", 66.0, 10.0, 0, {"1": "EN", "2": "GND"}),
    ("R4", "r", "10k", 72.0, 12.5, 0, {"1": "EN", "2": "3V3"}),
    ("C7", "c6", "1uF", 60.5, 12.5, 0, {"1": "EN", "2": "GND"}),
    ("C5", "c6", "100nF", 69.0, 15.5, 0, {"1": "3V3", "2": "GND"}),
    ("C6", "c8", "10uF", 74.5, 15.0, 0, {"1": "3V3", "2": "GND"}),
    ("SW2", "sw", "BOOT", 66.0, 45.0, 0, {"1": "IO0", "2": "GND"}),
    ("SW3", "sw", "USER", 44.0, 45.0, 0, {"1": "BTN", "2": "GND"}),
]


def build():
    board = pcbnew.CreateEmptyBoard()
    nets = {}
    for n in NETS:
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
    for ref, kind, val, x, y, rot, padnets in PARTS:
        lib, name = FP[kind]
        fp = pcbnew.FootprintLoad(LIB + lib + ".pretty", name)
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetPosition(v2i(x, y))
        fp.SetOrientation(ang(rot))
        if kind == "esp":
            # drop the 0.2 mm thermal vias from the EPAD: below the 0.3 mm min drill of cheap 2-layer fabs
            for p in list(fp.Pads()):
                if p.GetDrillSize().x > 0:
                    fp.Remove(p)
        for p in fp.Pads():
            nm = p.GetNumber()
            if nm in padnets:
                p.SetNet(nets[padnets[nm]])
        fp.Value().SetVisible(False)
        if ref[0] in "RC" or ref in ("J1", "J3"):
            fp.Reference().SetVisible(False)
        else:
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(FM(0.8), FM(0.8)))
            fp.Reference().SetTextThickness(FM(0.12))
        board.Add(fp)
    outline(board)
    set_rules(board)
    add_text(board)
    add_keepout(board)
    board.Save(OUT)
    return board


def outline(board):
    w = FM(0.1)
    def line(a, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(a); s.SetEnd(b); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(w); board.Add(s)
    def arc(cx, cy, a0):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
        pts = [v2i(cx + RC * math.cos(math.radians(a0 + k)), cy + RC * math.sin(math.radians(a0 + k)))
               for k in (0, 45, 90)]
        s.SetArcGeometry(*pts); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(w); board.Add(s)
    line(v2i(RC, 0), v2i(W - RC, 0)); arc(W - RC, RC, 270)
    line(v2i(W, RC), v2i(W, H - RC)); arc(W - RC, H - RC, 0)
    line(v2i(W - RC, H), v2i(RC, H)); arc(RC, H - RC, 90)
    line(v2i(0, H - RC), v2i(0, RC)); arc(RC, RC, 180)


def set_rules(board):
    ds = board.GetDesignSettings()
    ds.m_MinThroughDrill = FM(0.3)
    ds.m_HoleClearance = FM(0.15)
    ds.m_HoleToHoleMin = FM(0.25)
    ds.m_CopperEdgeClearance = FM(0.2)
    ds.m_TrackMinWidth = FM(0.15)
    ds.m_ViasMinSize = FM(0.5)
    ds.m_MinSilkTextHeight = FM(0.6)
    ns = ds.m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetClearance(FM(0.2)); d.SetTrackWidth(FM(0.25)); d.SetViaDiameter(FM(0.6)); d.SetViaDrill(FM(0.3))
    pw = pcbnew.NETCLASS("Power")
    pw.SetClearance(FM(0.2)); pw.SetTrackWidth(FM(0.4)); pw.SetViaDiameter(FM(0.6)); pw.SetViaDrill(FM(0.3))
    ns.SetNetclass("Power", pw)
    for n in ("VBUS", "VBAT", "3V3"):
        ns.SetNetclassPatternAssignment(n, "Power")


def txt(board, s, x, y, size, layer=pcbnew.F_SilkS, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s); t.SetPosition(v2i(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(FM(size), FM(size))); t.SetTextThickness(FM(size / 8))
    t.SetMirrored(mirror)
    board.Add(t)


def add_text(board):
    txt(board, "YOUR NAME", 44, 50.5, 2.0)
    txt(board, "EN", 66, 6.0, 0.8); txt(board, "BOOT", 66, 41.0, 0.8); txt(board, "USER", 44, 41.0, 0.8)
    txt(board, "OLED", 14, 17.0, 0.8)
    txt(board, "LiPo battery here (stick on back)", 40, 27, 1.0, pcbnew.B_SilkS, True)
    txt(board, "JST-PH: pin1 = +  (check polarity!)", 40, 31, 0.9, pcbnew.B_SilkS, True)


def add_keepout(board):
    ka = pcbnew.ZONE(board)
    ka.SetIsRuleArea(True)
    ka.SetDoNotAllowZoneFills(True); ka.SetDoNotAllowTracks(True); ka.SetDoNotAllowVias(True)
    ka.SetDoNotAllowPads(False); ka.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    ka.SetLayerSet(ls)
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for p in [(KEEPOUT_X, -1), (W + 1, -1), (W + 1, H + 1), (KEEPOUT_X, H + 1)]:
        ch.Append(v2i(*p))
    ch.SetClosed(True)
    ka.AddPolygon(ch)
    ka.SetZoneName("antenna_keepout")
    board.Add(ka)


def add_pours(board):
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        ls = pcbnew.LSET(); ls.AddLayer(layer); z.SetLayerSet(ls)
        z.SetNet(gnd)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefSpokeWidth(FM(0.3)); z.SetThermalReliefGap(FM(0.25))
        z.SetMinThickness(FM(0.2))
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for p in [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)]:
            ch.Append(v2i(*p))
        ch.SetClosed(True)
        z.AddPolygon(ch)
        board.Add(z)


def route():
    board = pcbnew.LoadBoard(OUT)
    for t in list(board.GetTracks()):
        board.RemoveNative(t)
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.RemoveNative(z)
    if not pcbnew.ExportSpecctraDSN(board, DSN):
        print("DSN export failed"); return 2
    if os.path.exists(SES): os.remove(SES)
    cmd = ["java", "-jar", JAR, "-de", DSN, "-do", SES, "-mp", "60"]
    try:
        p = subprocess.run(cmd, cwd=HERE, timeout=int(os.environ.get("ROUTE_TIMEOUT", "300")),
                           capture_output=True, text=True)
        print("\n".join((p.stdout + p.stderr).strip().splitlines()[-8:]))
    except subprocess.TimeoutExpired:
        print("freerouting timeout")
    if not os.path.exists(SES):
        print("no SES"); return 3
    if not pcbnew.ImportSpecctraSES(board, SES):
        print("SES import failed"); return 4
    add_pours(board)
    set_rules(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(OUT)
    tr = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vi = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    print("routed: %d segments, %d vias" % (len(tr), len(vi)))
    return 0


if __name__ == "__main__":
    build()
    print("built", OUT)
    if "--noroute" not in sys.argv:
        sys.exit(route())
