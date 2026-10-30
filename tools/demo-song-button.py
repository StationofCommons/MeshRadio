#!/usr/bin/env python3
"""Bench demo: button + NeoPixel ring + speaker, all in one.

Press the button (GPIO 17 to ground) to start a song. The song loops until the
button is pressed again. While it plays, the ring follows the music in colour: a
rainbow flows around it, the flow speeds up on every beat, the lit part grows and
shrinks smoothly with the loudness, and a soft glow swells across the whole ring
on strong beats. It is drawn at 60 frames per second, separately from the audio
readings, with eased changes, gamma and dithering so fades do not step.
The button's RGB light (GPIO 22, 23, 24), if wired, shows the same colour.

The song is not part of the repo. Put your own file on the Pi and pass it with
--song (default: ~/meshradio-demo/song.flac).

  tools/demo-song-button.py                 wait for button presses
  tools/demo-song-button.py --self-test 15  play 15 s with no button, print a report

Needs: python3-gi, gir1.2-gstreamer-1.0, python3-spidev, python3-gpiozero.
The ring is driven over SPI (GPIO 10), see docs/wiring.md.
"""
import argparse
import colorsys
import math
import os
import re
import signal
import sys
import time

import gi
import spidev

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

N = 24                 # pixels on the ring
MAX_LEVEL = 110        # out of 255 per colour. Keeps the ring dim and the current low
FPS = 60
GAMMA = 2.2
BUTTON_GPIO = 17
BUTTON_RGB_GPIO = (22, 23, 24)   # red, green, blue; common pin to ground
CONF = "/etc/meshradio/station.conf"


def read_conf(path):
    conf = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    conf[key] = value.strip('"')
    except OSError:
        pass
    return conf


class Ring:
    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 6_400_000
        self.spi.mode = 0

    def show(self, pixels):
        data = []
        for r, g, b in pixels:
            for byte in (g, r, b):
                for bit in range(7, -1, -1):
                    data.append(0xF8 if (byte >> bit) & 1 else 0xC0)
        data += [0] * 100
        self.spi.xfer3(data)

    def off(self):
        self.show([(0, 0, 0)] * N)

    def close(self):
        self.off()
        self.spi.close()


def ease(dt, tau):
    """Fraction of the remaining distance to cover in dt seconds."""
    return 1 - math.exp(-dt / tau)


class Animator:
    """Smooth ring animation. feed() takes loudness readings from the audio,
    render() is called every frame and returns the pixels."""

    def __init__(self):
        self.avg = 1e-4          # slow average of the energy
        self.peak = 1e-3         # slow-decaying maximum, to normalise the level
        self.norm = 0.0          # latest loudness, 0..1
        self.level = 0.0         # eased loudness
        self.fill = 2.0          # eased number of lit pixels (fractional)
        self.pulse = 0.0         # soft swell on beats, 0..1
        self.pulse_rise = 0.0    # seconds left of the rising phase
        self.hue = 0.0           # position on the colour wheel
        self.hue_boost = 0.0     # extra spin speed after a beat, decays
        self.last_beat = 0.0
        self.beats = 0
        self.readings = 0
        self.max_db = -120.0
        self.color = (0.0, 0.0, 0.0)               # for the button light
        self.err = [[0.0, 0.0, 0.0] for _ in range(N)]   # dither carry

    def feed(self, db):
        now = time.time()
        self.readings += 1
        self.max_db = max(self.max_db, db)
        lin = 10 ** (db / 20)
        self.peak = max(lin, self.peak * 0.997)
        self.norm = min(1.0, lin / self.peak)
        if lin > 1.35 * self.avg and now - self.last_beat > 0.22 and self.norm > 0.3:
            self.pulse_rise = 0.07
            self.hue_boost = 0.5
            self.last_beat = now
            self.beats += 1
        self.avg = 0.93 * self.avg + 0.07 * lin

    def render(self, dt):
        # loudness: quick to rise, slow to fall
        tau = 0.05 if self.norm > self.level else 0.28
        self.level += (self.norm - self.level) * ease(dt, tau)
        self.fill += (max(2.0, self.level * N) - self.fill) * ease(dt, 0.09)
        # beat swell: a short smooth rise, then a long smooth fall
        if self.pulse_rise > 0:
            self.pulse += (1.0 - self.pulse) * ease(dt, 0.025)
            self.pulse_rise -= dt
        else:
            self.pulse += (0.0 - self.pulse) * ease(dt, 0.30)
        # colours flow all the time and speed up after a beat
        self.hue_boost *= math.exp(-dt / 0.45)
        self.hue = (self.hue + (0.05 + self.hue_boost) * dt) % 1.0

        base = 0.18 + 0.82 * max(self.pulse, self.level * 0.6)
        pixels = []
        for i in range(N):
            coverage = min(1.0, max(0.0, self.fill - i))   # soft edge on the last pixel
            bright = coverage * base + (1 - coverage) * self.pulse * 0.35
            lin = bright ** GAMMA
            r, g, b = colorsys.hsv_to_rgb((self.hue + i / N) % 1.0, 1.0, 1.0)
            out = []
            for c, v in enumerate((r, g, b)):
                want = v * lin * MAX_LEVEL + self.err[i][c]
                whole = int(want)
                self.err[i][c] = want - whole     # carry the rest to the next frame
                out.append(whole)
            pixels.append(tuple(out))
        self.color = colorsys.hsv_to_rgb(self.hue, 1.0, base)
        return pixels


class Demo:
    def __init__(self, song, device, button_light):
        Gst.init(None)
        self.ring = Ring()
        self.anim = Animator()
        self.light = button_light
        self.pipeline = None
        self.loop = GLib.MainLoop()
        self.song = song
        self.device = device
        self.last_toggle = 0.0
        self.errors = []
        self.timer = None
        self.last_frame = 0.0
        self.frames = 0
        self.render_started = 0.0

    def build(self):
        return Gst.parse_launch(
            f'filesrc location="{self.song}" ! decodebin ! audioconvert ! audioresample '
            "! volume volume=0.5 ! tee name=t "
            f"t. ! queue ! audioconvert ! audioresample ! audio/x-raw,rate=48000,channels=2 "
            f"! alsasink device={self.device} "
            "t. ! queue ! audioconvert ! audio/x-raw,channels=1 "
            "! level interval=20000000 ! fakesink sync=true"
        )

    @property
    def playing(self):
        return self.pipeline is not None

    def start(self):
        if self.playing:
            return
        self.anim = Animator()
        self.frames = 0
        self.render_started = self.last_frame = time.time()
        self.timer = GLib.timeout_add(int(1000 / FPS), self.render)
        self.pipeline = self.build()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.pipeline.set_state(Gst.State.PLAYING)
        print("playing", flush=True)

    def stop(self):
        if not self.playing:
            return
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline = None
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = None
        self.ring.off()
        if self.light:
            self.light.value = (0, 0, 0)
        print("stopped", flush=True)

    def render(self):
        if not self.playing:
            return False
        now = time.time()
        dt = min(0.1, now - self.last_frame)
        self.last_frame = now
        self.ring.show(self.anim.render(dt))
        self.frames += 1
        if self.light:
            self.light.value = self.anim.color
        return True

    def toggle(self):
        now = time.time()
        if now - self.last_toggle < 0.3:
            return False
        self.last_toggle = now
        if self.playing:
            self.stop()
        else:
            self.start()
        return False  # for GLib.idle_add

    def on_message(self, _bus, msg):
        if not self.playing:
            return
        kind = msg.type
        if kind == Gst.MessageType.ELEMENT:
            s = msg.get_structure()
            if s and s.get_name() == "level":
                m = re.search(r"rms=\(GValueArray\)< ([-0-9.e]+)", s.to_string())
                if m:
                    self.anim.feed(float(m.group(1)))
        elif kind == Gst.MessageType.EOS:
            # loop: back to the start
            self.pipeline.seek_simple(
                Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0
            )
        elif kind == Gst.MessageType.ERROR:
            err, _dbg = msg.parse_error()
            self.errors.append(err.message)
            print("error:", err.message, flush=True)
            self.stop()

    def shutdown(self, *_):
        self.stop()
        self.loop.quit()

    def close(self):
        self.stop()
        self.ring.close()
        if self.light:
            self.light.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--song", default=os.path.expanduser("~/meshradio-demo/song.flac"))
    ap.add_argument("--device", default=read_conf(CONF).get("AUDIO_OUT", "default"))
    ap.add_argument("--self-test", type=float, metavar="SECONDS",
                    help="play for SECONDS without the button and print a report")
    ap.add_argument("--no-button-light", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.song):
        sys.exit(f"Song not found: {args.song}")

    light = None
    if not args.no_button_light:
        try:
            from gpiozero import RGBLED
            light = RGBLED(*BUTTON_RGB_GPIO, pwm=True)
        except Exception as e:  # the light is optional
            print("button light unavailable:", e)

    demo = Demo(args.song, args.device, light)
    signal.signal(signal.SIGTERM, demo.shutdown)
    signal.signal(signal.SIGINT, demo.shutdown)

    button = None
    if args.self_test:
        GLib.idle_add(demo.start)
        GLib.timeout_add(int(args.self_test * 1000), lambda: demo.shutdown() or False)
    else:
        from gpiozero import Button
        button = Button(BUTTON_GPIO, pull_up=True, bounce_time=0.05)
        button.when_pressed = lambda: GLib.idle_add(demo.toggle)
        print(f"ready: press the button (GPIO {BUTTON_GPIO}) to start or stop {args.song}",
              flush=True)

    try:
        demo.loop.run()
    finally:
        a = demo.anim
        demo.close()
        if button:
            button.close()
        if args.self_test:
            seconds = max(0.001, demo.last_frame - demo.render_started)
            print(f"frames sent to the ring: {demo.frames} ({demo.frames / seconds:.0f} per second)")
            print(f"audio readings:          {a.readings}")
            print(f"beats detected:          {a.beats}")
            print(f"loudest reading:         {a.max_db:.1f} dB")
            print(f"errors:                  {demo.errors or 'none'}")


if __name__ == "__main__":
    main()
