#!/usr/bin/env bash
# MeshRadio station installer.
#
# Run from a clone of the repo, as a normal user (sudo is used where needed):
#   ./install.sh [--station N] [--yes] [--enable-services] [--force] [--dry-run]
#
# It detects the Pi model (4 or 5) and asks for the station number before it
# installs anything. Then it installs the packages, the scripts and the systemd
# units, and writes /etc/meshradio/station.conf.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOTAL_STATIONS="${TOTAL_STATIONS:-5}"
MESH_NET="10.0.0"
CONF_DIR="/etc/meshradio"
CONF_FILE="$CONF_DIR/station.conf"

STATION_ID=""
ASSUME_YES=0
ENABLE_SERVICES=0
FORCE=0
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: ./install.sh [options]
  --station N         station number (1-$TOTAL_STATIONS); asked if not given
  --yes               do not ask for confirmation
  --enable-services   start the mesh, relay and button at boot
  --force             install on a model other than Pi 4 or Pi 5
  --dry-run           print what would be done and change nothing
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --station) STATION_ID="${2:-}"; shift 2 ;;
    --yes) ASSUME_YES=1; shift ;;
    --enable-services) ENABLE_SERVICES=1; shift ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

run() {
  if [ "$DRY_RUN" -eq 1 ]; then echo "[dry-run] $*"; else "$@"; fi
}

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as a normal user, not root. It calls sudo when needed."
  exit 1
fi

# --- Which Pi is this? -------------------------------------------------------
MODEL="$({ tr -d '\0' < /proc/device-tree/model; } 2>/dev/null || echo unknown)"
case "$MODEL" in
  *"Raspberry Pi 5"*) PI=5 ;;
  *"Raspberry Pi 4"*) PI=4 ;;
  *) PI=other ;;
esac
echo "Detected: $MODEL"
if [ "$PI" = other ]; then
  if [ "$FORCE" -eq 1 ]; then
    echo "Not a Pi 4 or 5. Continuing because of --force; the Pi 5 packages are used."
  else
    echo "MeshRadio supports the Raspberry Pi 4 and 5. Use --force to install anyway."
    exit 1
  fi
fi

# --- Which station? ----------------------------------------------------------
valid_station() {
  [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge 1 ] && [ "$1" -le "$TOTAL_STATIONS" ]
}

if [ -n "$STATION_ID" ] && ! valid_station "$STATION_ID"; then
  echo "--station must be a number between 1 and $TOTAL_STATIONS."
  exit 1
fi
while [ -z "$STATION_ID" ]; do
  read -r -p "Station number for this device (1-$TOTAL_STATIONS): " answer
  if valid_station "$answer"; then STATION_ID="$answer"; else
    echo "Enter a number between 1 and $TOTAL_STATIONS."
  fi
done

NEXT_ID=$(( STATION_ID % TOTAL_STATIONS + 1 ))
MESH_IP="$MESH_NET.$STATION_ID"
NEXT_HOP_IP="$MESH_NET.$NEXT_ID"

echo
echo "Station:        $STATION_ID of $TOTAL_STATIONS"
echo "Mesh IP:        $MESH_IP"
echo "Sends audio to: station $NEXT_ID ($NEXT_HOP_IP)"
echo
if [ "$ASSUME_YES" -ne 1 ]; then
  read -r -p "Continue with the full install? [y/N] " answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Cancelled. Nothing was installed."
    exit 0
  fi
fi

# --- Packages ----------------------------------------------------------------
# Pi 5 needs the lgpio backend for gpiozero; RPi.GPIO does not work on it.
# The Pi 4 also gets lgpio, plus RPi.GPIO as a fallback.
PACKAGES=(
  gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
  gstreamer1.0-plugins-bad gstreamer1.0-alsa alsa-utils
  batctl iw rfkill
  python3-gpiozero python3-lgpio
)
if [ "$PI" = 4 ]; then
  PACKAGES+=(python3-rpi.gpio)
fi

run sudo apt update
run sudo apt install -y "${PACKAGES[@]}"
run sudo usermod -aG audio,gpio "$USER"

# --- Audio devices -----------------------------------------------------------
# Prefer a USB card. Otherwise take the first card that is not HDMI. The Pi 4
# 3.5 mm jack is output only, so a Pi 4 still needs a USB card for the mic.
detect_card() {
  local tool="$1" list card
  list="$("$tool" -l 2>/dev/null | grep '^card ' || true)"
  card="$(grep -i 'usb' <<<"$list" | head -n1 | sed -E 's/^card ([0-9]+):.*/\1/' || true)"
  if [ -z "$card" ]; then
    card="$(grep -viE 'hdmi|vc4' <<<"$list" | head -n1 | sed -E 's/^card ([0-9]+):.*/\1/' || true)"
  fi
  echo "$card"
}

IN_CARD="$(detect_card arecord)"
OUT_CARD="$(detect_card aplay)"
if [ -z "$IN_CARD" ] || [ -z "$OUT_CARD" ]; then
  echo "Warning: no USB audio device found. Plug one in and edit AUDIO_IN and AUDIO_OUT in $CONF_FILE."
fi
AUDIO_IN="plughw:${IN_CARD:-0},0"
AUDIO_OUT="plughw:${OUT_CARD:-0},0"

# --- Station config ----------------------------------------------------------
CONF_TEXT="$(cat <<CONF
# MeshRadio station config. Written by install.sh on $(date +%F).
STATION_ID=$STATION_ID
TOTAL_STATIONS=$TOTAL_STATIONS
PI_MODEL=$PI
MESH_IP=$MESH_IP
NEXT_HOP_IP=$NEXT_HOP_IP

# Mesh: every station uses the same SSID, channel and BSSID.
WIFI_IF=wlan0
MESH_SSID=meshradio
MESH_FREQ=2412
MESH_BSSID=02:CA:FF:EE:BA:BE

# Audio
AUDIO_IN=$AUDIO_IN
AUDIO_OUT=$AUDIO_OUT
RTP_PORT=5000
JITTER_MS=150
HOP_VOLUME=0.85

# Button between this GPIO pin and ground
BUTTON_GPIO=17
CONF
)"

run sudo mkdir -p "$CONF_DIR"
if [ -f "$CONF_FILE" ]; then
  run sudo cp "$CONF_FILE" "$CONF_FILE.bak"
fi
if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] write $CONF_FILE:"; echo "$CONF_TEXT"
else
  echo "$CONF_TEXT" | sudo tee "$CONF_FILE" > /dev/null
fi

# --- Scripts and services ----------------------------------------------------
for script in meshradio-mesh-up meshradio-relay meshradio-button; do
  run sudo install -m 755 "$REPO_DIR/scripts/$script" /usr/local/bin/"$script"
done

for unit in meshradio-mesh meshradio-relay meshradio-button; do
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] install /etc/systemd/system/$unit.service (User=$USER)"
  else
    sed "s/@USER@/$USER/" "$REPO_DIR/systemd/$unit.service" \
      | sudo tee /etc/systemd/system/"$unit.service" > /dev/null
  fi
done
run sudo systemctl daemon-reload

if [ "$ENABLE_SERVICES" -ne 1 ] && [ "$ASSUME_YES" -ne 1 ]; then
  echo
  echo "Starting the mesh at boot takes the Wi-Fi away from normal use."
  echo "Keep Ethernet or a console connected, or you will lose SSH."
  read -r -p "Start the mesh, relay and button at boot? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] && ENABLE_SERVICES=1
fi
if [ "$ENABLE_SERVICES" -eq 1 ]; then
  run sudo systemctl enable meshradio-mesh meshradio-relay meshradio-button
fi

echo
echo "Done. Station $STATION_ID installed on a Raspberry Pi $PI."
if [ "$ENABLE_SERVICES" -eq 1 ]; then
  echo "Reboot to start the mesh."
else
  echo "Services are not enabled. To try the mesh now:"
  echo "  sudo meshradio-mesh-up up       # and 'down' to undo it"
  echo "  meshradio-relay                 # receive, play and forward"
  echo "  meshradio-button                # hold-to-talk"
fi
echo "Log out and back in once so the audio and gpio groups apply."
