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

## Not tested yet

- Three or more stations, and multi-hop routing
- Range, walls and crowds, and the Wi-Fi channel to use at ZKM
- The mesh coming back after a reboot with `meshradio-mesh.service`
- `meshradio-relay` and `meshradio-button` running as services
- Two-way use: one station speaking while it relays (needs an `audiomixer`)
- A Pi 4
- BATMAN_V
- The full `install.sh` on a station (only `--dry-run` was run)

## Notes from the bench

- `gst-launch-1.0` output can be lost when piped. Write it to a file and read that.
- Sending to the same UDP port from two sources at one station mixes two RTP streams in one jitter buffer. This is the reason the `audiomixer` is on the to-do list.
- The Pi 5 has no analog audio. The USB interface worked without drivers.
- A Mac cannot join the mesh, because batman-adv is a Linux kernel module. To program the Pis from a computer, use Ethernet or normal Wi-Fi.
