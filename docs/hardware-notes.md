# Hardware notes

Parts and options looked at while building the first two stations. Nothing here is a decision unless it says so. Check prices and stock yourself.

## Bought and in use

| Part | Notes |
|---|---|
| Raspberry Pi 5 (8 GB), two boards | owl-station-1 and cat-station-2 |
| Creative Sound Blaster Play! 3 (USB) | Works on a Pi 5. The microphone clips at full gain, see `test-log.md` |
| 16 mm RGB pushbutton, 5 V | Switch tested. Light not working yet. See `wiring.md` |
| Adafruit NeoPixel ring, 24 LEDs | Wired, driven over SPI. See `wiring.md` |
| Small speaker with a 3.5 mm cable and a USB power plug | USB carries power only |

## Audio

- The Pi 5 has no analogue audio jack, so it needs a USB sound card or a HAT. The Pi 4's 3.5 mm jack is output only, so it also needs a microphone input from a USB card.
- A cheap USB adapter works if it has separate microphone and headphone jacks (not one combined headset jack) and its mic level is acceptable. Test each model before buying five.
- The speaker needs its USB plug powered. A separate 5 V charger avoids hum from sharing the Pi's supply.

## Wi-Fi and the mesh

- The onboard Wi-Fi of the Pi 5 joined the batman-adv mesh in ad-hoc mode. Range is not tested.
- **Debug and gateway idea.** One extra Pi, outside the ring, sits in the mesh and also has Ethernet, with `bat0` and `eth0` bridged. That would give access to every station through one cable. It would share airtime with the audio, so switch it off for the piece itself. A third Pi does this job better than a travel router: same software, and the router's Wi-Fi is 2.4 GHz only, the same band as the mesh.
- A USB Wi-Fi dongle on each station would be a second radio for maintenance on normal Wi-Fi, so the mesh radio is never taken away.

## USB layout inside a case

The Pi 5's USB ports cannot be moved without rework. Options:

- Short extension cable, or a panel-mount USB-A extension for the speaker's power plug.
- Right-angle adapters, for example the Renkforce 90 degree models at Digitec and Galaxus.
- A 180 degree U-shape adapter, so the dongle lies back along the board. At Digitec and Galaxus only the "down" version exists: PowerGuard USB-A to USB-A, item 42089289. Mount the Pi so "down" has room, or turn the Pi over.
- A Pi Zero 2 W has USB pads on the underside that can be soldered to, if a very small station is wanted.

## Power

- The Pi 5 wants a 5 A supply (the official 27 W one). The Pimoroni LiPo SHIM gives only 1.5 A, so it is not enough for a Pi 5.
- Battery options rated for a Pi 5: Waveshare UPS HAT (E), 6 A, USB-C PD, four 21700 cells; Geekworm X1200 (2 x 18650) and X1202 (4 x 18650); DFRobot Pi 5 UPS HAT (4 x 18650); SunFounder PiPower 5. Check that the board leaves the header pins free.
- For an unattended installation, mains power is safer than batteries.
