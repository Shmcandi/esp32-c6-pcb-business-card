import pcbnew, sys
LIB = r"C:/Program Files/KiCad/10.0/share/kicad/footprints/"
for lib, name in [("RF_Module", "ESP32-S3-WROOM-1"),
                  ("Connector_USB", "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"),
                  ("Connector_JST", "JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal"),
                  ("Button_Switch_SMD", "SW_SPST_PTS810"),
                  ("Package_TO_SOT_SMD", "SOT-23-5"),
                  ("Connector_PinSocket_2.54mm", "PinSocket_1x04_P2.54mm_Vertical")]:
    fp = pcbnew.FootprintLoad(LIB + lib + ".pretty", name)
    if fp is None:
        print("MISSING", lib, name); continue
    bb = fp.GetBoundingBox(False, False)
    print("==", name, "bbox mm", pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
    if "WROOM" in name or "USB" in name or "JST" in name:
        for p in fp.Pads():
            c = p.GetPosition(); s = p.GetSize()
            print(" ", p.GetNumber(), round(pcbnew.ToMM(c.x), 2), round(pcbnew.ToMM(c.y), 2),
                  round(pcbnew.ToMM(s.x), 2), round(pcbnew.ToMM(s.y), 2), "drill" if p.GetDrillSize().x else "")
