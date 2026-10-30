# Wiring

Pin numbers are the physical pins on the Raspberry Pi 5's 40-pin header (the Pi 4 has the same layout). GPIO logic is **3.3 V** and the pins are not 5 V tolerant. Wire everything with the Pi powered off.

```
  odd pins (inner column)                even pins (outer column, board edge)

   1  3V3                                  2  5V      <- ring PWR
   3  GPIO 2                                4  5V
   5  GPIO 3                                6  GND     <- ring GND, button C
   7  GPIO 4                                8  GPIO 14
   9  GND      <- button S2                10  GPIO 15
  11  GPIO 17  <- button S1                12  GPIO 18
  13  GPIO 27                              14  GND
  15  GPIO 22  <- button R                 16  GPIO 23  <- button G
  17  3V3                                  18  GPIO 24  <- button B
  19  GPIO 10  <- ring IN (data)           20  GND
```

Hold the board with the USB and Ethernet ports at the bottom. The header runs down the right edge, with pin 1 at the top of the inner column and pin 2 at the top of the outer column. The table below is the authoritative list.

## Wire list

| Part | Part pin | Pi pin | GPIO | Notes |
|---|---|---|---|---|
| Button switch | S1 | 11 | GPIO 17 | Internal pull-up, no resistor. Which switch pin goes where does not matter |
| Button switch | S2 | 9 | GND | |
| Button light | C (common cathode) | 6 | GND | Not yet verified, see below |
| Button light | R | 15 | GPIO 22 | |
| Button light | G | 16 | GPIO 23 | |
| Button light | B | 18 | GPIO 24 | |
| NeoPixel ring | PWR | 2 | 5 V | |
| NeoPixel ring | GND | 6 | GND | |
| NeoPixel ring | IN | 19 | GPIO 10 (SPI MOSI) | About 330 ohm resistor in the data line. Leave the ring's OUT pad empty |

Nothing else uses these pins. The sound card is on USB.

## Parts

| Part | Link |
|---|---|
| Button: PureCrea 16 mm raised pushbutton, RGB light, 5 V, stainless steel, 6 pins | https://www.galaxus.ch/en/s4/product/purecrea-16mm-raised-pushbutton-with-rgb-illumination-5v-stainless-steel-buttons-switches-43800716 |
| Ring: Adafruit NeoPixel ring, 24 x WS2812 5050 | https://www.galaxus.ch/en/s1/product/adafruit-neopixel-ring-24-x-ws2812-5050-rgb-led-diode-5998261 |
| Sound card: Creative Sound Blaster Play! 3 (USB) | https://www.galaxus.ch/en/s1/product/creative-sound-blaster-play3-usb-30-carte-son-6999374 |

## Button

The button has 6 pins: two for the switch (S1, S2), a common pin (C) and one pin per colour (R, G, B).

- **Switch: tested.** It needs no external resistor, because the internal pull-up of GPIO 17 is enabled in software (`gpiozero`, `pull_up=True`). It reads 0 V when pressed and 3.3 V when released. `tools/button-test.py` printed clean press and release events (69 events over 20 s).
- **Light: not working yet.** The listing says the light's resistors are rated for 5 V and that 3.3 V also works. We assumed a **common cathode** (C to ground), so a colour turns on when its GPIO pin is high. With only blue wired, GPIO 22 to 24 were confirmed high by `pinctrl`, but no light was seen. Possible causes: the blue wire is on the wrong pin, the common pin is not touching ground, or the button is a common anode. To check polarity safely, connect C to pin 1 (3V3) and a colour pin to ground. If it lights, it is a common anode, and the software must drive the pins low instead.

If the light has no built-in resistors, put about 220 ohm in each colour wire.

## NeoPixel ring

- **Driver.** The common `rpi_ws281x` library does not support the Pi 5. The ring is driven over SPI from GPIO 10 with plain `spidev` (`python3-spidev`), at 6.4 MHz. Each WS2812 bit is sent as one SPI byte (`0xF8` for 1, `0xC0` for 0), colour order GRB, followed by a run of zero bytes as the reset. SPI was already enabled on both bench Pis.
- **Logic level.** The ring's chips run at 5 V and want a data signal of about 3.5 V or more. The Pi sends 3.3 V. It often works. If the ring flickers or shows wrong colours, add a level shifter (74AHCT125) or shorten the data wire.
- **Power.** About 50 mA per LED at full white, so up to roughly 1.2 A for 24 LEDs. The test scripts run at about 15 % brightness, which draws a few hundred milliamps and can use the Pi's 5 V pin. At full brightness, give the ring its own 5 V supply and join the grounds.
- **Status.** The test scripts (`tools/ring-test.py`, `tools/ring-rainbow.py`) ran without errors. The colours on the ring were not confirmed by eye in the session, so treat the ring as wired but not verified.

## Speaker

The bench speaker has a 3.5 mm audio cable and a USB plug. The USB plug carries **power only**. The audio goes through the Sound Blaster's green (output) jack, and the microphone goes into the pink (input) jack. The speaker made no sound until its USB plug was connected to a power source. For the installation, power it from a small 5 V charger if hum appears when it shares the Pi's supply.

## Audio levels

The Sound Blaster's microphone clips at its default capture gain (100 %, +30 dB). See `docs/test-log.md`. Lower the capture gain to about half for clean speech.
