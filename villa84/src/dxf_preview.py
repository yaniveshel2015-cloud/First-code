"""Render a DXF to PNG with ezdxf's drawing add-on, to check the export visually."""
import sys

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

src, dst = sys.argv[1], sys.argv[2]
w = float(sys.argv[3]) if len(sys.argv) > 3 else 24
doc = ezdxf.readfile(src)
msp = doc.modelspace()
fig = plt.figure(figsize=(w, w * 0.7))
ax = fig.add_axes([0, 0, 1, 1])
cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR)
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp, finalize=True)
if len(sys.argv) > 7:
    x0, y0, x1, y1 = map(float, sys.argv[4:8])
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
fig.savefig(dst, dpi=110)
print("saved", dst)
