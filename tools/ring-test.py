#!/usr/bin/env python3
"""Light a 24-pixel WS2812 ring over SPI (GPIO 10). Dim on purpose."""
import time
import spidev

N = 24
LEVEL = 40  # about 15% of full brightness

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 6_400_000
spi.mode = 0


def show(pixels):
    data = []
    for r, g, b in pixels:
        for byte in (g, r, b):
            for bit in range(7, -1, -1):
                data.append(0xF8 if (byte >> bit) & 1 else 0xC0)
    data += [0] * 100
    spi.xfer3(data)


def fill(color):
    show([color] * N)


for color in ((LEVEL, 0, 0), (0, LEVEL, 0), (0, 0, LEVEL)):
    fill(color)
    time.sleep(1)
for i in range(N * 2):
    show([(LEVEL, LEVEL, LEVEL) if p == i % N else (0, 0, 0) for p in range(N)])
    time.sleep(0.05)
fill((0, 0, 0))
spi.close()
print("ring test done")
