# Bench tools

Small scripts for testing the hardware on one station. They are not installed by `install.sh`. Wiring is in [`../docs/wiring.md`](../docs/wiring.md).

| Script | What it does |
|---|---|
| `button-test.py` | Prints every press and release of the button on GPIO 17. |
| `ring-test.py` | Lights the NeoPixel ring in red, green, blue and white to check the wiring and colour order. |
| `ring-rainbow.py` | Runs a rainbow around the ring. |
| `demo-song-button.py` | The all-in-one demo: press the button to play a song and animate the ring (and the button light) with the music, press again to stop. `--self-test 15` runs it for 15 s without the button and prints a report. |

The demo needs `python3-gi`, `gir1.2-gstreamer-1.0`, `python3-spidev` and `python3-gpiozero`. Put your own audio file at `~/meshradio-demo/song.flac` or pass `--song`. Audio files are ignored by git and are not part of the repo.
