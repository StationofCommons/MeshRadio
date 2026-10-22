# MeshRadio

```
   ,___,       /\_/\       __        \|/ \|/      ><{{{(o>
   (O,O)      ( o.o )    <(o )___     \\ //
   /)__)       > ^ <       ( ._> /    (o.o)
   -"-"-                    `---'      \_/
  station 1   station 2   station 3  station 4   station 5
```

A relay station for the Station of Commons installation at ZKM. Each station is a Raspberry Pi 5 with a microphone, a speaker and a button. A visitor holds the button and speaks. The voice travels around a ring of stations over a Wi-Fi mesh, arriving at each one a little later and a little more distorted than at the last.

The same module is built five times for the pilot. Every station runs the same software, and only a short config file differs.

> **Status:** early development. Everything under "Test the audio hardware" and "Stream audio between two Pis" was tested on the bench. The ring relay, the mesh and the button are designs that have not been tested yet, and they are marked as such below.

## Two rules of the piece

1. **Nothing is recorded.** A station only relays a live stream. No audio is written to disk.
2. **The microphone opens on purpose.** It is live only while the button is held. The work never picks up surrounding sound without consent.

## How it works

```
 station 1 --> station 2 --> station 3 --> station 4 --> station 5
     ^                                                       |
     +-------------------------------------------------------+
```

- Every station can take a voice in and relays whatever arrives from the previous station.
- Each station sends to one fixed next station. The ring order is a curatorial choice made once at install time. The stations do not negotiate it.
- The audio is raw 48 kHz PCM sent as RTP over UDP. It is not compressed, so the delay at each station stays predictable.
- Delay comes from `rtpjitterbuffer`, with a floor of 150 ms per station. Real Wi-Fi jitter from distance and crowds adds to it. Dropped packets are meant to be heard as glitches and are not smoothed over.
- Each hop lowers the volume of the relayed signal (about 0.85), so a voice fades after a few trips round the ring.
- The stations find each other with **batman-adv**, a layer 2 mesh. There is no router and no internet. batman-adv only moves packets. It does not decide which station's audio goes where.

## Hardware (per station)

| Part | Notes |
|---|---|
| Raspberry Pi 5 (or 4) | Pi 5 has no analog audio jack, so it needs a USB audio device or a HAT |
| Audio in and out | One of the options below |
| USB Wi-Fi dongle, Atheros AR9271 | The Pi 5's onboard Wi-Fi is unreliable in ad-hoc mode. The Olimex MOD-WIFI-AR9271 uses the right chipset. Avoid TP-Link TL-WN722N unless it is v1 |
| Push button | Momentary, normally open |
| Directional speaker and amp | To be decided |
| microSD card and USB-C power supply | |

### Audio options

| Option | Input | Output | Pi 5 | Notes |
|---|---|---|---|---|
| Creative Sound Blaster Play! 3 (USB) | 3.5 mm mono mic | two 3.5 mm | untested | About CHF 18. Check the mic level and noise |
| Audient EVO 4 (USB) | XLR or TRS combo | headphone and monitor | untested | Class-compliant. Expensive for five stations |
| ReSpeaker 2-Mics Pi HAT **v2.0** | two onboard mics | 3.5 mm and speaker | documented | Needs a device tree overlay built by hand. v1 does not work on Pi 5 |
| UGREEN USB audio adapter | 3.5 mm | 3.5 mm | forum reports say yes | Plug and play |

### Button

Wire the button between a GPIO pin and ground. No resistor is needed, because the internal pull-up is enabled in software. Use `gpiozero`, not `RPi.GPIO`, which does not work correctly on Pi 5. If you use the ReSpeaker HAT, keep clear of the GPIO pins it uses.

## Setup

Requires a Raspberry Pi 5 or 4 running Raspberry Pi OS Trixie.

### 1. Install GStreamer

```bash
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-alsa
```

### 2. Test the audio hardware

List capture devices, then playback devices:

```bash
arecord -l
aplay -l
```

Note the card and device numbers. They are used below as `plughw:CARD,DEVICE`.

Test files:

- Short audio file: https://soccloud.dy.fi/index.php/s/gQj2REPx6Q9sEzF
- Long audio file: https://soccloud.dy.fi/index.php/s/TSWTHZkarkekGKy

### 3. Stream audio between two Pis (tested)

Send a file as MP3 over MPEG-TS. This is a quick bench test only. MP3 adds delay and is not used in the final design.

```bash
gst-launch-1.0 filesrc location=dj.mp3 ! decodebin ! audioconvert ! audioresample \
  ! audio/x-raw,rate=48000 ! lamemp3enc target=bitrate bitrate=128 cbr=true \
  ! mpegaudioparse ! mpegtsmux ! udpsink host=192.168.1.27 port=5000
```

Send from the audio input instead:

```bash
gst-launch-1.0 alsasrc device=plughw:1,0 ! decodebin ! audioconvert ! audioresample \
  ! audio/x-raw,rate=48000 ! lamemp3enc target=bitrate bitrate=128 cbr=true \
  ! mpegaudioparse ! mpegtsmux ! udpsink host=192.168.1.27 port=5000
```

Receive in VLC with `udp://@:5000`.

### 4. Raw RTP pipeline (draft, untested)

Send the microphone to the next station:

```bash
gst-launch-1.0 alsasrc device=plughw:1,0 ! audioconvert ! audioresample \
  ! audio/x-raw,format=S16BE,rate=48000,channels=1 ! rtpL16pay \
  ! udpsink host=NEXT_HOP_IP port=5000
```

Receive, play locally and forward at lower volume:

```bash
gst-launch-1.0 udpsrc port=5000 \
  caps="application/x-rtp,media=audio,clock-rate=48000,encoding-name=L16,channels=1,payload=96" \
  ! rtpjitterbuffer latency=150 drop-on-latency=false do-lost=true \
  ! rtpL16depay ! audioconvert ! tee name=t \
  t. ! queue ! audioresample ! alsasink device=plughw:2,0 \
  t. ! queue ! volume volume=0.85 ! audioconvert \
  ! audio/x-raw,format=S16BE,rate=48000,channels=1 ! rtpL16pay \
  ! udpsink host=NEXT_HOP_IP port=5000
```

Not done yet: an `audiomixer` that combines the local microphone with the incoming relay, so one station can both speak and relay.

## Mesh network (planned, untested)

batman-adv on a USB Wi-Fi dongle in ad-hoc mode, with a fixed IP on `bat0` for each station (for example 10.0.0.1 to 10.0.0.5). Test one Pi 5, one dongle and batman-adv before building five.

## Configuration (planned)

Each station reads a small config file. Only these values differ between stations:

```
STATION_ID=1
MESH_IP=10.0.0.1
NEXT_HOP_IP=10.0.0.2
```

Station 5 points back to station 1. This makes it possible to build one SD card image and clone it for all five stations.

## To do

- [ ] Choose and test the audio hardware on a Pi 5
- [ ] batman-adv mesh on two Pis, then five
- [ ] Raw RTP pipeline with `audiomixer` and per-hop volume
- [ ] Button script with `gpiozero`: hold to talk, with the pipeline running only while held
- [ ] systemd services so each station starts on boot, with a restart watchdog
- [ ] `install.sh` and a config file for cloning stations
- [ ] Calibrate the delay on site at ZKM
- [ ] Choose the directional speaker and amp
