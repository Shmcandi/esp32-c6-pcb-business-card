import re
import uuid

def uid():
    return str(uuid.uuid4())

with open('aio_card.kicad_pcb', 'r', encoding='utf-8') as f:
    content = f.read()

# Clean up any broken injected lines
idx_cut = content.find('(uuid "oled-')
if idx_cut != -1:
    content = content[:idx_cut].rstrip()
    if not content.endswith(')'):
        content += '\n)\n'

def line_sexpr(x0, y0, x1, y1, w=0.15, layer="F.SilkS"):
    return f"""\t(gr_line
\t\t(start {x0:.3f} {y0:.3f})
\t\t(end {x1:.3f} {y1:.3f})
\t\t(stroke
\t\t\t(width {w})
\t\t\t(type default)
\t\t)
\t\t(layer "{layer}")
\t\t(uuid "{uid()}")
\t)
"""

def rect_sexpr(x0, y0, x1, y1, w=0.15, layer="F.SilkS"):
    return (line_sexpr(x0, y0, x1, y0, w, layer) +
            line_sexpr(x1, y0, x1, y1, w, layer) +
            line_sexpr(x1, y1, x0, y1, w, layer) +
            line_sexpr(x0, y1, x0, y0, w, layer))

def text_sexpr(text, x, y, size=1.0, thick=0.15, layer="F.SilkS"):
    return f"""\t(gr_text "{text}"
\t\t(at {x:.3f} {y:.3f})
\t\t(layer "{layer}")
\t\t(uuid "{uid()}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size {size} {size})
\t\t\t\t(thickness {thick})
\t\t\t)
\t\t)
\t)
"""

# Let's generate the OLED graphics:
# J3 header is at x=18.0, y=19.38 to 32.08.
# Module PCB: 19.5 to 57.5, y=18.0 to 33.5
# Glass outline: 22.0 to 55.0, y=19.5 to 32.0
# Active display: 25.0 to 52.0, y=21.5 to 30.0

out = "\n"
out += rect_sexpr(19.5, 18.0, 57.5, 33.5, 0.20, "F.SilkS") # Module PCB outline
out += rect_sexpr(22.0, 19.5, 55.0, 32.0, 0.15, "F.SilkS") # Glass outline
out += rect_sexpr(25.0, 21.5, 52.0, 30.0, 0.12, "F.SilkS") # Active display screen
out += text_sexpr("0.91\" OLED (128x32)", 38.5, 24.5, 1.2, 0.16)
out += text_sexpr("SSD1306 SPI 6-PIN", 38.5, 27.2, 1.0, 0.13)

# Add pin indicators next to the J3 header pads
pins = ["1:GND", "2:3V3", "3:SCK", "4:MOSI", "5:RES", "6:DC"]
for i, p in enumerate(pins):
    y = 19.38 + i * 2.54
    out += text_sexpr(p, 13.0, y, 0.65, 0.10)

# Also on bottom silkscreen, show battery outline (30x25mm)
out += rect_sexpr(35.0, 16.0, 65.0, 41.0, 0.15, "B.SilkS")

idx_last = content.rfind(')')
new_content = content[:idx_last] + out + ')\n'

with open('aio_card.kicad_pcb', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OLED display graphics written successfully.')
