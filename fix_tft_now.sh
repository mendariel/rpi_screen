#!/bin/bash
# Quick-fix script for existing Volumio TFT kiosk installation
# Fixes 3 problems found in diagnostics:
#   1. Xorg.wrap blocks X from starting via systemd service
#   2. Xorg config points to /dev/fb1 which doesn't exist (TFT is on /dev/fb0)
#   3. .xinitrc has broken/empty variables

sudo mount -o remount,rw /

echo "=== Fix 1: Allow X server to run from systemd service ==="
sudo bash -c 'printf "allowed_users=anybody\nneeds_root_rights=yes\n" > /etc/X11/Xwrapper.config'
echo "Created /etc/X11/Xwrapper.config"

echo ""
echo "=== Fix 2: Point Xorg to correct framebuffer ==="
FB_DEV="/dev/fb0"
[ -e /dev/fb1 ] && FB_DEV="/dev/fb1"
echo "Using framebuffer: $FB_DEV"
sudo bash -c "cat > /etc/X11/xorg.conf.d/99-tft.conf <<EOF
Section \"Device\"
    Identifier \"TFT Screen\"
    Driver \"fbdev\"
    Option \"fbdev\" \"$FB_DEV\"
EndSection

Section \"Screen\"
    Identifier \"TFT\"
    Device \"TFT Screen\"
EndSection
EOF"
echo "Updated /etc/X11/xorg.conf.d/99-tft.conf"

echo ""
echo "=== Fix 3: Rewrite .xinitrc with correct variable escaping ==="
sudo bash -c 'cat > /home/volumio/.xinitrc <<'"'"'EOF'"'"'
# Display transformation for TFT screen
DISPLAY=:0 xinput set-prop 6 "Coordinate Transformation Matrix" -1 0 1 0 1 0 0 0 1 2>/dev/null || true

# Hide mouse cursor after inactivity
unclutter -idle 5 -root &

# Disable screen blanking and power management
xset s off
xset -dpms
xset s noblank

# Start idle monitor for clock screensaver
(
  IDLE_TIME=600  # seconds (10 minutes) - edit here to change
  CLOCK_SHOWN=0

  while true; do
    IDLE=$(xprintidle 2>/dev/null || echo 0)
    IDLE_SECONDS=$((IDLE / 1000))

    if [ $IDLE_SECONDS -gt $IDLE_TIME ] && [ $CLOCK_SHOWN -eq 0 ]; then
      CLOCK_SHOWN=1
      /usr/local/bin/volumio-clock.py &
      CLOCK_PID=$!

    elif [ $IDLE_SECONDS -le $IDLE_TIME ] && [ $CLOCK_SHOWN -eq 1 ]; then
      CLOCK_SHOWN=0
      kill $CLOCK_PID 2>/dev/null
      pkill -f "volumio-clock.py"
    fi

    sleep 1
  done
) &

# Wait for Volumio web server to be ready (up to 60 seconds)
for i in {1..30}; do
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    break
  fi
  sleep 2
done

# Start Chromium in kiosk mode
chromium --no-sandbox --disable-gpu --disable-software-rasterizer --disable-dev-shm-usage --kiosk http://localhost:3000
EOF'

sudo chmod 555 /home/volumio/.xinitrc
sudo chown volumio:volumio /home/volumio/.xinitrc
echo "Rewrote /home/volumio/.xinitrc"

echo ""
echo "=== Reloading systemd and restarting kiosk service ==="
sudo systemctl daemon-reload
sudo systemctl restart volumio-kiosk.service
sleep 5
echo ""
echo "=== Service status ==="
sudo systemctl status volumio-kiosk.service --no-pager -l

echo ""
echo "All fixes applied. If the status shows 'active (running)', the TFT should now show Chromium."
echo "If it still fails, reboot with: sudo reboot"
