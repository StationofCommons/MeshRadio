#!/usr/bin/env bash
# MeshRadio station installer.
# Asks which station this Pi is, then installs the packages and writes the
# station config. Run as a normal user; sudo is used where needed.
set -euo pipefail

TOTAL_STATIONS="${TOTAL_STATIONS:-5}"
MESH_NET="10.0.0"
CONF_DIR="/etc/meshradio"
CONF_FILE="$CONF_DIR/station.conf"

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as a normal user, not root. It calls sudo when needed."
  exit 1
fi

# Ask for the station number before anything is installed.
while true; do
  read -r -p "Station number for this device (1-$TOTAL_STATIONS): " STATION_ID
  if [[ "$STATION_ID" =~ ^[0-9]+$ ]] && [ "$STATION_ID" -ge 1 ] && [ "$STATION_ID" -le "$TOTAL_STATIONS" ]; then
    break
  fi
  echo "Enter a number between 1 and $TOTAL_STATIONS."
done

NEXT_ID=$(( STATION_ID % TOTAL_STATIONS + 1 ))
MESH_IP="$MESH_NET.$STATION_ID"
NEXT_HOP_IP="$MESH_NET.$NEXT_ID"

echo
echo "Station:        $STATION_ID of $TOTAL_STATIONS"
echo "Mesh IP:        $MESH_IP"
echo "Sends audio to: station $NEXT_ID ($NEXT_HOP_IP)"
echo
read -r -p "Continue with the full install? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Cancelled. Nothing was installed."
  exit 0
fi

sudo apt update
sudo apt install -y \
  gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-alsa python3-gpiozero batctl

sudo mkdir -p "$CONF_DIR"
sudo tee "$CONF_FILE" > /dev/null <<EOF
STATION_ID=$STATION_ID
TOTAL_STATIONS=$TOTAL_STATIONS
MESH_IP=$MESH_IP
NEXT_HOP_IP=$NEXT_HOP_IP
EOF

echo
echo "Done. Config written to $CONF_FILE:"
cat "$CONF_FILE"
echo
echo "Not set up yet: the batman-adv mesh, the audio pipeline service and the button script."
