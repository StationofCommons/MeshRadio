# Test log

Bench tests done on 2026-10-22 with two Raspberry Pi 5 boards. This records what was tried, what worked and what is still open.

## Setup

| | owl-station-1 | cat-station-2 |
|---|---|---|
| Board | Raspberry Pi 5 | Raspberry Pi 5 (8 GB) |
| OS | Raspberry Pi OS Trixie (Debian 13), desktop | Raspberry Pi OS Trixie, desktop, kernel 6.18 |
| Audio | Audient EVO 4 over USB (ALSA card 2, `plughw:2,0`) | none attached |
| Wi-Fi | onboard | onboard |

Both boards stayed on Ethernet during the mesh test so we could control them over SSH. The mesh ran on `wlan0`.

Software: GStreamer from the Debian packages, `batctl` 2025.0 and the batman-adv kernel module 2025.4.

## 1. Audio over a normal LAN

| Test | Result |
|---|---|
| Sine tone, owl to cat, raw L16 RTP, jitter buffer 150 ms | Pass. Level meter on the receiver read a steady -13.5 dB RMS, no lost packets |
| Tone played on owl through the EVO 4 | Pass, no errors |
| EVO 4 microphone, owl to cat | Arrived, but the level was very low (-56 to -67 dB). The gain knob on the EVO 4 was too low, not a software fault |

## 2. batman-adv mesh on the onboard Wi-Fi

Both Pis list IBSS (ad-hoc) as a supported mode and do not list mesh point (802.11s). The brcmfmac driver supports ad-hoc, so batman-adv runs on top of an ad-hoc network.

What was done on each Pi (this is what `meshradio-mesh-up up` does):

```
nmcli device set wlan0 managed no
ip link set wlan0 down
iw dev wlan0 set type ibss
ip link set wlan0 up
iw dev wlan0 set power_save off
iw dev wlan0 ibss join <ssid> 2412 fixed-freq <bssid>
modprobe batman-adv
batctl meshif bat0 interface add wlan0
ip link set up dev bat0
ip addr add 10.0.0.N/24 dev bat0
```

| Test | Result |
|---|---|
| Each Pi sees the other as a batman neighbour | Pass |
| `ping` over `bat0`, 50 packets | 0 % loss, average 16.5 ms (min 6.6, max 79, mdev 13.8) |
| `batctl ping` by MAC address | 5 of 5 replies |
| Raw RTP tone over the mesh, 10 level readings | All -13.5 dB, no loss |
| About 25 s of a stereo FLAC file, cat to owl over `bat0`, played on the EVO 4 | No errors in the pipelines. We did not confirm by ear that it was audible |
| Was Ethernet used? | No. During a 10 s stream the interface counters on cat-station-2 were: eth0 0 KB, wlan0 1,021 KB, bat0 1,001 KB |

The jitter in the ping times (6.6 to 79 ms) is typical of ad-hoc Wi-Fi on two boards a short distance apart. It is within what the 150 ms jitter buffer absorbs, and it is the kind of unevenness the piece is meant to let through.

## Routing algorithm

The mesh runs **BATMAN_IV**, the default. The kernel also offers **BATMAN_V**, which estimates link throughput. It was not tried. To try it, set the algorithm before `bat0` exists (`batctl routing_algo BATMAN_V`, or the `routing_algo` module parameter), then bring the mesh up again.

## 3. Installer on two Pi 5 stations (2026-10-30)

`install.sh` was run on both Pis from the repo contents, with `--station 1` on owl-station-1 and `--station 2` on cat-station-2. Both runs exited cleanly.

| Check | Result |
|---|---|
| Model detection | Both reported Raspberry Pi 5 Model B |
| Packages, scripts in `/usr/local/bin`, three systemd units, `/etc/meshradio/station.conf` | Installed on both |
| `systemd-analyze verify` on the units | No errors |
| Services at boot | Installed but not enabled, as intended |
| Updating from the repo and re-running | Worked. The config was rewritten and the old one kept as `station.conf.bak` |
| Audio device detection | Picked the Sound Blaster on both. Before a USB card was plugged into cat-station-2 it fell back to the HDMI card (card 0), which has no microphone. The installer now falls back to ALSA `default` and prints a warning |

Finding: `meshradio-relay.service` and `meshradio-button.service` both `Want` the mesh service, so starting either one also brings up the mesh. The mesh takes `wlan0`, so a Pi that is reachable only over Wi-Fi drops off the network. Keep Ethernet plugged in while testing over SSH. The installer's closing message now says this.

Not run: the mesh, relay and button as services on a ring.

## 4. Sound Blaster Play! 3 (USB), 2026-10-30

| Test | Result |
|---|---|
| Detected as a USB audio card on a Pi 5 | Pass, no driver needed (ALSA card 2). It has a capture and a playback side |
| Microphone, silence, capture gain 100 % (+30 dB) | Steady floor of about -62 dB RMS |
| Microphone, talking close to it, gain 100 % | Average about -9 to -14 dB RMS, peaks at 0 dB in nearly every reading. **It clips.** Lower the capture gain to about half for clean speech |
| Same test on a second card on cat-station-2 | Same result, so the two cards behave alike |
| Speaker on the green output jack | No sound until the speaker's USB plug was connected for power. Then a 440 Hz tone and the live microphone were heard |
| Microphone to speaker on the same Pi (about 8 s, and about 5 min) | Heard clearly, no feedback at low volume |
| Playback of a stereo FLAC file through the speaker | Run on owl-station-1. Heard result not recorded |

After a reboot ALSA restored the card's saved mixer state: speaker volume 47 %, capture gain 100 %.

## 5. Button and NeoPixel ring (2026-10-30)

Wiring is in [`wiring.md`](wiring.md). The scripts are in `tools/`.

| Test | Result |
|---|---|
| Button switch between GPIO 17 and ground, `tools/button-test.py` for 20 s | Pass. Idle read "not pressed", and 69 clean press and release events, each press about 0.2 to 0.5 s |
| NeoPixel ring over SPI, `tools/ring-test.py` and `tools/ring-rainbow.py` | Ran without errors on a Pi 5. SPI was already enabled. The colours on the ring were not confirmed by eye |
| Button light, blue wire only on GPIO 24 | **No light seen.** `pinctrl` showed GPIO 22, 23 and 24 driven high. Cause not found yet. Check wiring and whether the common pin is a cathode (ground) or an anode (3V3) |

## 6. Network and access notes

- Wi-Fi settings written from another computer while the Pi was running were lost after a power cut: the profile file was 0 bytes. Shut a Pi down with `sudo poweroff` and not by unplugging it.
- Raspberry Pi OS keeps logs in memory only by default, so the logs from before a reboot are gone. Enable persistent journaling if you need them.
- The repo was private during these tests, so the Pis cloned it with read-only deploy keys. Once the repo is public this is not needed.

## Not tested yet

- Three or more stations, and multi-hop routing
- Range, walls and crowds, and the Wi-Fi channel to use at ZKM
- The mesh coming back after a reboot with `meshradio-mesh.service`
- `meshradio-relay` and `meshradio-button` running as services
- Two-way use: one station speaking while it relays (needs an `audiomixer`)
- The button light and the colours of the NeoPixel ring (see above)
- Voice from one Pi to the other over the mesh, with the new Sound Blaster cards
- A Pi 4
- BATMAN_V
- The full `install.sh` on a station (only `--dry-run` was run)

## Notes from the bench

- `gst-launch-1.0` output can be lost when piped. Write it to a file and read that.
- Sending to the same UDP port from two sources at one station mixes two RTP streams in one jitter buffer. This is the reason the `audiomixer` is on the to-do list.
- The Pi 5 has no analog audio. The USB interface worked without drivers.
- A Mac cannot join the mesh, because batman-adv is a Linux kernel module. To program the Pis from a computer, use Ethernet or normal Wi-Fi.

## 7. All-in-one demo (button, ring, song)

`tools/demo-song-button.py` checks the button, the NeoPixel ring and the speaker together. Press the button to start a song, press again to stop. The ring shows a flowing rainbow that follows loudness and beats, drawn at 60 frames per second with eased changes, gamma and dithering. Self-test (`--self-test`, 12 s, no button): 747 frames (62 per second), 606 audio readings, 30 beats, no errors. The button light on GPIO 22 to 24 is optional and was not visible in our test, see `docs/wiring.md`. The song is the tester's own file and is not in the repo.
