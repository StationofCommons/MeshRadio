#!/usr/bin/env python3
"""Print each press and release of a button between GPIO 17 and ground."""
import sys
import time
from gpiozero import Button

seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 20
button = Button(17, pull_up=True, bounce_time=0.05)
start = time.time()
events = []
button.when_pressed = lambda: events.append((time.time() - start, "pressed"))
button.when_released = lambda: events.append((time.time() - start, "released"))
print("idle state:", "pressed" if button.is_pressed else "not pressed", flush=True)
time.sleep(seconds)
for t, e in events:
    print(f"{t:5.1f}s  {e}")
print(f"{len(events)} events")
