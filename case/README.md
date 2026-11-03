# Station case (3D printed)

A round puck, 110 mm across, for one Raspberry Pi 5 station. It is made of two printed parts plus a diffuser:

| Part | File | Notes |
|---|---|---|
| Base | `stl/puck_base.stl` | Tray with the Pi 5 standoffs and the port cut-outs |
| Lid | `stl/puck_lid.stl` | Plate with the ring recess, the button pedestal and a wire slot |
| Diffuser | `stl/puck_diffuser.stl` | Own 7.5 mm cap, printed in natural or white translucent filament |

Not printed: the Raspberry Pi 5 with its cooler, a 24-LED NeoPixel ring (66 mm outside diameter), the Adafruit 3350 button with its washer and nut, and four M2.5 screws.

The shapes are written in [CadQuery](https://cadquery.readthedocs.io). The sizes are parameters at the top of `puck_case.py`.

## Rebuild the STL files

```
pip install cadquery ocp_vscode
python puck_case.py
```

The script exports the three STL files into the current folder. It also shows the model in the OCP CAD Viewer (VS Code extension `bernhard-42.ocp-cad-viewer`).

## Reference models (not in this repo)

The viewer script shows the real Pi, button and diffuser next to the case. Those files belong to other people and are not included. Download them into the folders below, next to `puck_case.py`:

| Folder | File | Source | Licence |
|---|---|---|---|
| `ref-button/` | `button3350.step` | [Adafruit CAD parts](https://github.com/adafruit/Adafruit_CAD_Parts) | MIT |
| `ref-pi5/` | `pi5-607854.stp` | [Printables 607854](https://www.printables.com/model/607854-raspberry-pi-5) | GPL v2 |
| `ref-pi5/` | `pi5-with-cooler.stl` | [Printables 727155](https://www.printables.com/model/727155-raspberry-pi-5) | CC0 |
| `ref-diffuser/` | `LEDringUHR.stl` | [Printables 336208](https://www.printables.com/model/336208-led-ring-diffuser-121624xneopixel) | CC0 |

The Printables diffuser is 25 mm tall and fits the 24-LED ring. You can print it instead of `puck_diffuser.stl`.

## Status

Not printed yet. Still open: nothing holds the Sound Blaster or the speaker, nothing fastens the lid to the base, and the fit of the ring in the diffuser is unchecked on a real part.
