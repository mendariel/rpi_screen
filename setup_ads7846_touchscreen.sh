
#!/bin/bash

# ADS7846 Touchscreen Setup Script for Raspberry Pi (Debian)
# This script configures the touchscreen calibration and makes it persistent

# Exit on error
set -e

# Check for root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Define calibration file path
CALIB_FILE="/etc/X11/xorg.conf.d/99-calibration.conf"

# Create calibration config
echo "Creating calibration config at $CALIB_FILE..."
mkdir -p /etc/X11/xorg.conf.d
cat <<EOF > "$CALIB_FILE"
Section "InputClass"
    Identifier      "calibration"
    MatchProduct    "ADS7846 Touchscreen"
    Option  "SwapXY"        "0"      # Do not swap X and Y axes
    Option  "InvertX"       "0"      # X-axis is correct
    Option  "InvertY"       "1"      # Flip Y-axis
EndSection
EOF

# Lock the file to prevent overwrites (optional)
echo "Locking calibration file to prevent changes..."
chattr +i "$CALIB_FILE"

# Restart X11 to apply changes
echo "Restarting X11..."
pkill Xorg || echo "Xorg not running or already stopped"

# Done
echo "Touchscreen calibration applied successfully."
