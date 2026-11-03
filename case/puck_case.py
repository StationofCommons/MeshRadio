"""MeshRadio station case: round puck, Pi 5 inside, NeoPixel ring on top, button in the middle.

Parts (dimensions from retailer listings, check with calipers before printing):
  Adafruit NeoPixel Ring 24: outer 66 mm, inner 52.4 mm, 3.5 mm thick.
  PureCrea 16 mm raised RGB button: 16 mm hole, body about 21.5 mm long, panel 1 to 7 mm.
  Raspberry Pi 5: 85 x 56 mm, holes 58 x 49 mm.

The ring sits face up in a shallow recess on top of the lid. A separate diffuser cap (a hollow,
raised ring with a thin top) covers it. Print the cap in natural or white PETG for a soft glow,
and the base and lid in any colour. The cap goes on after the ring is in place.
Run this file to export the STLs and show the model, with the parts in grey for checking fit.
"""
import math
import cadquery as cq

import os
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape

try:
    from ocp_vscode import show
except ImportError:
    show = None

# --- Parts ---
RING_OD, RING_ID, RING_T = 66.0, 52.4, 3.5
BTN_HOLE, BTN_LEN = 16.2, 21.5      # hole with clearance, body length below the panel
WASHER_T, WASHER_OD = 1.0, 19.0       # washer / seal on the outside, under the button flange
BTN_HEAD = 1.5                      # flat head above the panel (Adafruit 3350 model)
PED_D, PED_TOP, PED_BORE = 32.0, 23.5, 24.0   # pedestal that lifts the button to the diffuser top
BOARD_X, BOARD_Y, BOARD_T = 85.0, 56.0, 1.4
HOLE_DX, HOLE_DY, HOLE_FROM_LEFT, HOLE_D = 58.0, 49.0, 3.5, 2.7
COOLER_H = 17.0                     # active cooler above the board, rough
# Positions from the official Pi 5 mechanical drawing (RP-007222): sockets 11.2, 25.8, 39.2 mm from
# the left on the bottom edge; Ethernet 10.2, USB stacks 29.1 and 47 mm from the bottom on the right
# edge, which overhangs the board by 3 mm. Cut-outs are sized for the plugs, not the sockets.
PORTS_BOTTOM = [(11.2, 13.0, 7.0), (25.8, 10.0, 6.5), (39.2, 10.0, 6.5)]      # USB-C, micro HDMI x2
PORTS_RIGHT = [(10.2, 16.5, 14.5), (29.1, 16.5, 16.5), (47.0, 16.5, 16.5)]    # Ethernet, USB stacks

# --- Case ---
WALL, FLOOR, CLEAR = 2.4, 2.4, 0.6
STANDOFF_H, STANDOFF_D = 5.0, 6.0
LID_T = 3.0                         # lid plate thickness
RING_FIT = 0.4                      # recess clearance around the ring
RECESS = 1.0                        # how deep the ring sits into the lid
CAP_WALL = 1.0                      # side walls of the diffuser cap
CAP_TOP = 1.0                       # thin top skin that diffuses the light
CAP_AIR = 4.0                       # gap between the LEDs and the top skin
LIP_H, LIP_T = 3.0, 1.6

diag = math.hypot(BOARD_X, BOARD_Y)
OUTER_D = math.ceil(diag + 2 * (CLEAR + WALL) + 2)     # round, so the Pi corners fit
INNER_D = OUTER_D - 2 * WALL
z_cooler_top = FLOOR + STANDOFF_H + BOARD_T + COOLER_H
# the button now sits on a pedestal, so only its tail reaches below the lid: keep 3 mm above the cooler
INNER_H = math.ceil(max(z_cooler_top + 3 - FLOOR, BTN_LEN - PED_TOP - LID_T + 3 + 3))
z_lid = FLOOR + INNER_H            # underside of the lid

left, bottom = -BOARD_X / 2, -BOARD_Y / 2
holes = [(left + HOLE_FROM_LEFT + dx, bottom + 3.5 + dy) for dx in (0, HOLE_DX) for dy in (0, HOLE_DY)]
z_board = FLOOR + STANDOFF_H + BOARD_T

# Base: round tray with standoffs and port cut-outs
base = (cq.Workplane("XY").circle(OUTER_D / 2).extrude(z_lid)
        .faces(">Z").workplane().circle(INNER_D / 2).cutBlind(-INNER_H))
standoffs = (cq.Workplane("XY").workplane(offset=FLOOR).pushPoints(holes)
             .circle(STANDOFF_D / 2).extrude(STANDOFF_H)
             .faces(">Z").workplane().pushPoints(holes).hole(HOLE_D, STANDOFF_H - 0.5))
base = base.union(standoffs)
for x_from_left, w, h in PORTS_BOTTOM:
    base = base.cut(cq.Workplane("XY").box(w, 30, h).translate(
        (left + x_from_left, bottom - 15 + 1, z_board + h / 2 - 0.5)))
for y_from_bottom, w, h in PORTS_RIGHT:
    base = base.cut(cq.Workplane("XY").box(30, w, h).translate(
        (BOARD_X / 2 + 15 - 1, bottom + y_from_bottom, z_board + h / 2 - 0.5)))

# Lid: plate with the button hole in the middle, a shallow recess for the ring, a wire slot, a lip
r_in, r_out = RING_ID / 2 - RING_FIT / 2, RING_OD / 2 + RING_FIT
lid = cq.Workplane("XY").workplane(offset=z_lid).circle(OUTER_D / 2).extrude(LID_T)
recess = (cq.Workplane("XY").workplane(offset=z_lid + LID_T - RECESS)
          .circle(r_out).circle(r_in).extrude(RECESS + 1))
lid = lid.cut(recess)
# pedestal in the middle: hollow below, a 3 mm top plate with the button hole
pedestal = cq.Workplane("XY").workplane(offset=z_lid).circle(PED_D / 2).extrude(LID_T + PED_TOP)
lid = lid.union(pedestal)
lid = lid.cut(cq.Workplane("XY").workplane(offset=z_lid - 1).circle(PED_BORE / 2).extrude(1 + LID_T + PED_TOP - 3))
lid = lid.cut(cq.Workplane("XY").workplane(offset=z_lid + LID_T + PED_TOP - 4).circle(BTN_HOLE / 2).extrude(6))
# slot for the ring's three wires, move it to where your pads are
lid = lid.cut(cq.Workplane("XY").workplane(offset=z_lid - 1).center(0, r_in + 3).rect(10, 5).extrude(LID_T + 2))
lip = (cq.Workplane("XY").workplane(offset=z_lid - LIP_H)
       .circle(INNER_D / 2 - 0.2).circle(INNER_D / 2 - 0.2 - LIP_T).extrude(LIP_H))
lid = lid.union(lip)

# Diffuser cap: a hollow raised ring that sits over the LEDs
cap_h = RING_T - RECESS + CAP_AIR + CAP_TOP
cap = (cq.Workplane("XY").workplane(offset=z_lid + LID_T)
       .circle(r_out + CAP_WALL).circle(r_in - CAP_WALL).extrude(cap_h)
       .cut(cq.Workplane("XY").workplane(offset=z_lid + LID_T - 0.01)
            .circle(r_out).circle(r_in).extrude(cap_h - CAP_TOP + 0.01)))

# Reference parts, not printed. The button is Adafruit's own CAD model (product 3350, MIT licence,
# github.com/adafruit/Adafruit_CAD_Parts): z = 0 is the panel top, flange 18 mm, thread body 14 mm,
# 1.5 mm flat head, 21.5 mm in all with the pins. It comes without the nut and washer.
BTN_STEP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref-button", "button3350.step")
ring = (cq.Workplane("XY").workplane(offset=z_lid + LID_T - RECESS)
        .circle(RING_OD / 2).circle(RING_ID / 2).extrude(RING_T))
button = (cq.Workplane("XY").workplane(offset=z_lid + LID_T + PED_TOP - BTN_LEN).circle(BTN_HOLE / 2 - 0.1)
          .extrude(BTN_LEN + BTN_HEAD))
def block(x_from_left, y_from_bottom, w, d, h, z0):
    """Box with its centre at (x, y) measured from the board's bottom-left corner."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .box(w, d, h, centered=(True, True, False))
            .translate((left + x_from_left, bottom + y_from_bottom, 0)))

if os.path.exists(BTN_STEP):
    button = cq.importers.importStep(BTN_STEP).val().moved(cq.Location(cq.Vector(0, 0, z_lid + LID_T + PED_TOP + WASHER_T)))
# Colours for studio mode: black head and flange, metallic thread body, rear block and pins
button_head = button_body = None
if os.path.exists(BTN_STEP):
    try:
        z_btn = z_lid + LID_T + PED_TOP + WASHER_T
        solids = cq.importers.importStep(BTN_STEP).solids().vals()
        above = cq.Workplane("XY").box(60, 60, 10, centered=(True, True, False)).translate((0, 0, -0.05))
        s0 = cq.Workplane("XY").add(solids[0])
        lift = cq.Location(cq.Vector(0, 0, z_btn))
        button_head = cq.Compound.makeCompound([s0.intersect(above).val(), solids[2]]).moved(lift)
        button_body = cq.Compound.makeCompound([s0.cut(above).val(), solids[1], *solids[3:]]).moved(lift)
    except Exception as e:  # fall back to the single grey button
        print("button colour split failed:", e)
        button_head = button_body = None

washer = (cq.Workplane("XY").workplane(offset=z_lid + LID_T + PED_TOP)
          .circle(WASHER_OD / 2).circle(BTN_HOLE / 2 - 0.1).extrude(WASHER_T))
pi = (cq.Workplane("XY").workplane(offset=z_board - BOARD_T)
      .box(BOARD_X, BOARD_Y, BOARD_T, centered=(True, True, False)))
for x, w, h in [(11.2, 9.0, 3.2), (25.8, 7.5, 3.4), (39.2, 7.5, 3.4)]:          # USB-C, micro HDMI x2
    pi = pi.union(block(x, 3.0, w, 7.5, h, z_board))
pi = pi.union(block(BOARD_X - 18.2 / 2 + 3 / 2, 10.2, 18.2, 16.0, 13.5, z_board))            # Ethernet
for y in (29.1, 47.0):                                                                         # USB stacks
    pi = pi.union(block(BOARD_X - 17.0 / 2 + 3 / 2, y, 17.0, 14.8, 16.2, z_board))
pi = pi.union(block(32.5, 52.5, 51.0, 5.1, 8.5, z_board))                                      # GPIO header
cooler = block(29.0, 28.0, 40, 40, COOLER_H, z_board)      # rough, the SoC is near the middle

# Fit check: nothing of the board, connectors or cooler may touch the base
for name, part in [("Pi + connectors", pi), ("cooler", cooler)]:
    hit = base.intersect(part).val().Volume() if base.intersect(part).vals() else 0.0
    print(f"fit check, {name} inside base: {'OK' if hit < 0.5 else f'COLLIDES ({hit:.0f} mm3)'}")

# The Printables diffuser (CC0, https://www.printables.com/model/336208), used as is, for the
# 24 LED ring: 25 mm tall, flares from 68 mm at the bottom to 102 mm at the top, empty centre.
# Print the downloaded STL itself. It only needs to sit on the lid, centred on the ring.
DIFFUSER_STL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref-diffuser", "LEDringUHR.stl")
diffuser = None
if os.path.exists(DIFFUSER_STL):
    diffuser = TopoDS_Shape()
    StlAPI_Reader().Read(diffuser, DIFFUSER_STL)
    diffuser = cq.Shape.cast(diffuser).moved(cq.Location(cq.Vector(0, 0, z_lid + LID_T - 0.1)))

# Real Pi 5 with active cooler (Printables model 727155, CC0). Its Y axis is up and its USB-C side
# is at +Z, so turn it 90 degrees about X; the PCB bottom goes on top of the standoffs.
PI_STL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref-pi5", "pi5-with-cooler.stl")
pi_model = None
if os.path.exists(PI_STL):
    topo = TopoDS_Shape()
    StlAPI_Reader().Read(topo, PI_STL)
    pi_model = (cq.Shape.cast(topo).rotate((0, 0, 0), (1, 0, 0), 90)
                .moved(cq.Location(cq.Vector(0, 0, z_board - BOARD_T))))
    # fit check on the mesh points: anything beyond the inner wall must be a connector in a cut-out
    from vtkmodules.vtkIOGeometry import vtkSTLReader
    from vtkmodules.util.numpy_support import vtk_to_numpy
    rd = vtkSTLReader(); rd.SetFileName(PI_STL); rd.Update()
    pts = vtk_to_numpy(rd.GetOutput().GetPoints().GetData())
    x, y = pts[:, 0], -pts[:, 2]
    r = (x ** 2 + y ** 2) ** 0.5
    out = r > INNER_D / 2 - 0.3
    print(f"Pi mesh: {int(out.sum())} points reach the inner wall; max radius {r.max():.1f} mm "
          f"(inner wall {INNER_D / 2:.1f} mm)")

# Second Pi 5 model for comparison (Printables 607854, GPL v2, STEP; the author had not yet seen a real board)
PI2_STEP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref-pi5", "pi5-607854.stp")
pi_compare = None
if os.path.exists(PI2_STEP):
    pi_compare = cq.importers.importStep(PI2_STEP).val().moved(cq.Location(cq.Vector(0, 0, z_board - BOARD_T)))
from threejs_materials import PbrProperties, PbrValues


def pbr(key, rgb, metalness, roughness):
    return PbrProperties(id=key, name=key, source="custom", url="", license="n/a",
                         values=PbrValues(color=list(rgb), metalness=metalness, roughness=roughness))


MATERIALS = {   # shown in the viewer's studio mode
    "button head (black)": pbr("button-black", (0.02, 0.02, 0.02), 0.2, 0.35),
    "button body (metal)": pbr("button-metal", (0.8, 0.8, 0.82), 1.0, 0.25),
}

# Coloured Pi 5: the 607854 STEP keeps a colour per part (green PCB, silver ports, black chips).
# The other Pi 5 models on Printables are STL files, which cannot hold colours.
USE_COLORED_PI = True
pi_colored = None
if USE_COLORED_PI and os.path.exists(PI2_STEP):
    pi_colored = cq.Assembly.importStep(PI2_STEP)
    pi_colored.loc = cq.Location(cq.Vector(0, 0, z_board - BOARD_T))

SHOW_COMPARE = False  # show it next to the first model, shifted 120 mm to the side

SHOW_TOP = True    # also show the lid, diffuser, ring and button, placed beside the base
TOP_OFFSET = 130   # how far to the side (mm); set SHOW_TOP = False to hide them

if __name__ == "__main__":
    cq.exporters.export(base, "puck_base.stl")
    cq.exporters.export(lid, "puck_lid.stl")
    cq.exporters.export(cap, "puck_diffuser.stl")
    print(f"puck: {OUTER_D} mm wide, {z_lid + LID_T + PED_TOP:.1f} mm tall to the button panel, diffuser cap adds {cap_h:.1f} mm")
    if show:
        try:
            top = diffuser if diffuser is not None else cap
            parts = [(base, "base")]
            parts += [(pi_colored, "pi5 (coloured, Printables 607854)")] if pi_colored is not None else \
                     [(pi_model, "pi5 + cooler (Printables)")] if pi_model is not None else \
                     [(pi, "pi5 (ref)"), (cooler, "cooler (ref)")]
            if SHOW_TOP:
                side = cq.Location(cq.Vector(TOP_OFFSET, 0, 0))
                btn = ([(button_head, "button head (black)"), (button_body, "button body (metal)")]
                       if button_head is not None else [(button, "button (ref)")])
                parts += [(p.moved(side) if hasattr(p, "moved") else p.val().moved(side), n)
                          for p, n in [(lid, "lid"), (top, "diffuser"), (ring, "ring (ref)"), *btn, (washer, "washer (ref)")]]
            if SHOW_COMPARE and pi_compare is not None:
                parts += [(pi_compare.moved(cq.Location(cq.Vector(120, 0, 0))), "pi5 (Printables 607854)"),
                          (pi_model.moved(cq.Location(cq.Vector(120, 0, 0))), "pi5 + cooler (727155), same spot")]
            names = [n for _, n in parts]
            mats = [MATERIALS.get(n) for n in names]
            extra = {"materials": mats} if any(m is not None for m in mats) else {}
            show(*[p for p, _ in parts], names=names, **extra)
        except Exception as e:
            print("viewer not reachable:", e)
