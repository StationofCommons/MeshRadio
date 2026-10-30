#!/usr/bin/env python3
"""Rotating rainbow on a 24-pixel WS2812 ring over SPI (GPIO 10). Dim on purpose."""
import colorsys
import signal
import sys
import time
import spidev

N = 24
LEVEL = 0.16  # fraction of full brightness
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 10

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


def rainbow(offset):
    pixels = []
    for i in range(N):
        r, g, b = colorsys.hsv_to_rgb(((i / N) + offset) % 1.0, 1.0, LEVEL)
        pixels.append((int(r * 255), int(g * 255), int(b * 255)))
    return pixels


signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

try:
    start = time.time()
    while time.time() - start < SECONDS:
        show(rainbow(((time.time() - start) * 0.3) % 1.0))
        time.sleep(0.02)
finally:
    show([(0, 0, 0)] * N)
    spi.close()
