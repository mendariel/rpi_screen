#!/bin/bash

# Volumio TFT Display + Clock Screensaver Setup Script
# For Raspberry Pi 3 with 3.5" TFT Touchscreen
# This script sets up both the TFT display and adds clock screensaver functionality

echo "======================================"
echo "Volumio TFT Display + Screensaver Setup"
echo "======================================"
echo ""

# Remount root filesystem as read-write
sudo mount -o remount,rw /

# Install all required packages (combined from both scripts)
echo "Installing required packages..."
sudo apt-get update
sudo apt-get install -y matchbox-window-manager x11-xserver-utils xinput xserver-xorg xserver-xorg-video-fbdev xinit xfonts-base xfonts-100dpi xfonts-75dpi chromium chromium-common chromium-sandbox chromium-codecs-ffmpeg python3-tk xprintidle xdotool unclutter curl

# Remove old/conflicting packages
echo "Cleaning up old dependencies..."
sudo apt-get remove -y xscreensaver xscreensaver-gl-extra xterm 2>/dev/null || true
sudo apt-get autoremove -y

# Remount /boot as read-write
sudo mount -o remount,rw /boot

# Disable vc4 KMS/FKMS in /boot/config.txt (conflicts with fbdev TFT setups)
echo "Disabling vc4-kms overlays (conflicts with TFT fbdev driver)..."
sudo sed -i 's/^\(dtoverlay=vc4-kms-v3d.*\)/#\1/' /boot/config.txt
sudo sed -i 's/^\(dtoverlay=vc4-fkms-v3d.*\)/#\1/' /boot/config.txt

# Set overlays in /boot/userconfig.txt
USERCONFIG=/boot/userconfig.txt

echo "Configuring TFT display and touchscreen..."
# Remove any previous overlays
sudo sed -i '/^dtoverlay=iqaudio-dacplus/d' $USERCONFIG
sudo sed -i '/^dtoverlay=iqaudio-digiampplus/d' $USERCONFIG
sudo sed -i '/^dtparam=audio=on/d' $USERCONFIG
sudo sed -i '/^dtoverlay=piscreen/d' $USERCONFIG
sudo sed -i '/^dtoverlay=ads7846/d' $USERCONFIG
sudo sed -i '/^dtoverlay=vc4-fkms-v3d/d' $USERCONFIG
sudo sed -i '/^dtoverlay=vc4-kms-v3d/d' $USERCONFIG

# Add overlays for TFT and touchscreen
echo "dtoverlay=ads7846,cs=1,speed=500000,penirq=25,swapxy=1" | sudo tee -a $USERCONFIG
echo "dtoverlay=piscreen,rotate=90" | sudo tee -a $USERCONFIG

# Blacklist vc4 kernel module to prevent GPU driver from conflicting with fbdev TFT
# Note: On Volumio, devicetree force-loads vc4 so blacklisting alone doesn't prevent it,
# but combined with Xorg ServerLayout + AutoAddGPU=false it prevents modesetting usage.
echo "Blacklisting vc4 kernel module..."
sudo bash -c 'printf "blacklist vc4\nblacklist drm_display_helper\n" > /etc/modprobe.d/blacklist-vc4.conf'

# Create Xorg configuration to force X server onto TFT framebuffer
echo "Creating Xorg configuration for TFT framebuffer..."
sudo mkdir -p /etc/X11/xorg.conf.d/

# Use existing framebuffer: fb1 if present, otherwise fb0
FB_DEV="/dev/fb0"
[ -e /dev/fb1 ] && FB_DEV="/dev/fb1"
sudo tee /etc/X11/xorg.conf.d/99-tft.conf > /dev/null << 'XORGEOF'
Section "ServerFlags"
    Option "AutoAddDevices" "true"
    Option "AutoEnableDevices" "true"
    Option "AutoAddGPU" "false"
EndSection

Section "Device"
    Identifier "TFT Screen"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
EndSection

Section "Screen"
    Identifier "TFT"
    Device "TFT Screen"
EndSection

Section "ServerLayout"
    Identifier "Default Layout"
    Screen "TFT"
EndSection
XORGEOF

# Volumio uses SquashFS overlay - deleted system files restore on reboot.
# Instead of deleting conflicting Xorg configs, overwrite them with harmless content.
echo "Neutralizing conflicting Xorg configs (SquashFS-safe overwrites)..."
echo "# Disabled by volumio-tft-setup - original vc4 OutputClass removed" | sudo tee /etc/X11/xorg.conf.d/99-v3d.conf > /dev/null
echo "# Disabled by volumio-tft-setup" | sudo tee /usr/share/X11/xorg.conf.d/20-noglamor.conf > /dev/null
echo "# Disabled by volumio-tft-setup" | sudo tee /usr/share/X11/xorg.conf.d/00-glamor.conf > /dev/null

# Allow X server from systemd service (non-console user)
echo "Configuring Xwrapper..."
sudo bash -c 'printf "allowed_users=anybody\nneeds_root_rights=yes\n" > /etc/X11/Xwrapper.config'

# Ask user about DigiAMP+ HAT
echo ""
echo "Audio Configuration:"
echo "==================="
echo "Do you want to enable IQaudIO Pi-DigiAMP+ HAT (AMP HAT) audio output?"
echo "1) No (default: HDMI/Headphones)"
echo "2) Yes (enable DigiAMP+ and disable onboard audio)"
read -p "Enter 1 or 2 [default: 1]: " audio_choice
if [[ "$audio_choice" == "2" ]]; then
  echo "dtoverlay=iqaudio-dacplus" | sudo tee -a $USERCONFIG
  echo "#dtparam=audio=on" | sudo tee -a $USERCONFIG
  echo "IQaudIO Pi-DigiAMP+ overlay added. Onboard audio disabled."
fi

# Configuration variables for screensaver
SCREENSAVER_TIMEOUT=300  # 5 minutes (in seconds)

# Ask user for screensaver timeout
echo ""
echo "Screensaver Configuration:"
echo "=========================="
echo "The clock will display after idle time and stay on until you touch the screen."
echo ""
read -p "Enter screensaver timeout in minutes [default: 5]: " timeout_input
if [[ ! -z "$timeout_input" ]]; then
  SCREENSAVER_TIMEOUT=$((timeout_input * 60))
fi

# Create Python clock screensaver
echo "Creating custom clock screensaver..."
sudo bash -c 'cat > /usr/local/bin/volumio-clock.py <<'\''PYCLOCK'\''
#!/usr/bin/env python3
import tkinter as tk
from datetime import datetime
import random
import os

# Set display
os.environ["DISPLAY"] = ":0"

class ClockScreensaver:
    def __init__(self):
        self.root = tk.Tk()
        # Make window always on top and truly fullscreen
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        
        # Force update to get real screen dimensions
        self.root.update()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Set exact geometry to fill entire screen
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        
        self.root.bind("<Button-1>", self.quit)
        self.root.bind("<Key>", self.quit)
        self.root.bind("<Escape>", self.quit)
        self.root.bind("<Motion>", self.quit)
        
        # Create clock label with smaller initial font
        self.clock_label = tk.Label(
            self.root,
            font=("Arial", 40, "bold"),
            bg="black",
            fg="white"
        )
        
        # Movement variables - start in center
        self.x = max(50, self.screen_width // 2 - 100)
        self.y = max(50, self.screen_height // 2 - 80)
        self.dx = 1
        self.dy = 1
        
        # Place label and start updates
        self.clock_label.place(x=self.x, y=self.y)
        self.update_clock()
        self.root.mainloop()
    
    def update_clock(self):
        try:
            # Get current time
            now = datetime.now()
            time_str = now.strftime("%H:%M")
            day_str = now.strftime("%A")
            date_str = now.strftime("%B %d")
            
            # Update text
            self.clock_label.config(text=f"{time_str}\n{day_str}\n{date_str}")
            
            # Change color randomly every update
            colors = ["white", "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", 
                      "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739"]
            self.clock_label.config(fg=random.choice(colors))
            
            # Update label to get actual size
            self.clock_label.update_idletasks()
            label_width = self.clock_label.winfo_width()
            label_height = self.clock_label.winfo_height()
            
            # Move position slightly (1 pixel)
            self.x += self.dx
            self.y += self.dy
            
            # Bounce off edges with margin
            if self.x <= 5 or self.x >= self.screen_width - label_width - 5:
                self.dx = -self.dx
                self.x = max(5, min(self.x, self.screen_width - label_width - 5))
            if self.y <= 5 or self.y >= self.screen_height - label_height - 5:
                self.dy = -self.dy
                self.y = max(5, min(self.y, self.screen_height - label_height - 5))
            
            # Position the label
            self.clock_label.place(x=self.x, y=self.y)
            
        except Exception as e:
            print(f"Error: {e}")
        
        # Update every 3 seconds
        self.root.after(3000, self.update_clock)
    
    def quit(self, event=None):
        self.root.destroy()

if __name__ == "__main__":
    try:
        ClockScreensaver()
    except Exception as e:
        print(f"Failed to start clock: {e}")
        import traceback
        traceback.print_exc()
PYCLOCK'

sudo chmod +x /usr/local/bin/volumio-clock.py

# Create combined .xinitrc with both TFT calibration and screensaver functionality
echo "Creating combined .xinitrc configuration..."
sudo bash -c 'cat > /home/volumio/.xinitrc <<EOF
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
  IDLE_TIME='$SCREENSAVER_TIMEOUT'  # User-defined timeout in seconds
  CLOCK_SHOWN=0
  
  while true; do
    IDLE=\$(xprintidle 2>/dev/null || echo 0)
    IDLE_SECONDS=\$((IDLE / 1000))
    
    if [ \$IDLE_SECONDS -gt \$IDLE_TIME ] && [ \$CLOCK_SHOWN -eq 0 ]; then
      # Show Python clock screensaver
      CLOCK_SHOWN=1
      /usr/local/bin/volumio-clock.py &
      CLOCK_PID=\$!
      
    elif [ \$IDLE_SECONDS -le \$IDLE_TIME ] && [ \$CLOCK_SHOWN -eq 1 ]; then
      # Hide clock
      CLOCK_SHOWN=0
      kill \$CLOCK_PID 2>/dev/null
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

# Set proper permissions and ownership
sudo chmod 555 /home/volumio/.xinitrc
sudo chown volumio:volumio /home/volumio/.xinitrc

# Mask getty on tty1 so kiosk service can own the VT
echo "Masking getty@tty1..."
sudo systemctl stop getty@tty1 2>/dev/null || true
sudo systemctl disable getty@tty1 2>/dev/null || true
sudo systemctl mask getty@tty1

# Create systemd service for kiosk
echo "Creating systemd service..."
sudo bash -c 'cat > /etc/systemd/system/volumio-kiosk.service <<EOF
[Unit]
Description=Volumio Kiosk on TFT
After=network-online.target
Wants=network-online.target
Conflicts=getty@tty1.service

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=FRAMEBUFFER=/dev/fb0
TTYPath=/dev/tty1
StandardInput=tty
StandardOutput=tty
StandardError=journal
ExecStartPre=/bin/sleep 15
ExecStart=/usr/bin/startx /home/volumio/.xinitrc -- :0 vt1 -keeptty
User=volumio
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF'

# Enable the service (but don't start it yet - will start after reboot)
sudo systemctl daemon-reload
sudo systemctl enable volumio-kiosk.service

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "TFT Display Configuration:"
echo "- 3.5\" TFT with touchscreen support"
echo "- 90-degree rotation applied"
echo "- Touch calibration configured"
if [[ "$audio_choice" == "2" ]]; then
  echo "- IQaudIO Pi-DigiAMP+ HAT enabled"
  echo "- Onboard audio disabled"
else
  echo "- Default audio (HDMI/Headphones) enabled"
fi
echo ""
echo "Screensaver Configuration:"
echo "- Clock screensaver activates after: $((SCREENSAVER_TIMEOUT/60)) minutes of inactivity"
echo "- Clock stays on until you touch the screen"
echo "- Screen never blanks (clock always visible)"
echo "- Shows: Time, Day, Date (updates every 3 seconds)"
echo "- Touch screen to return to Volumio"
echo "- Mouse cursor hides after 5 seconds"
echo ""
echo "Services:"
echo "- volumio-kiosk.service (enabled, will start after reboot)"
echo ""
echo "Post-Reboot Commands:"
echo "- Check status: sudo systemctl status volumio-kiosk.service"
echo "- View logs: sudo journalctl -u volumio-kiosk.service"
echo "- Restart service: sudo systemctl restart volumio-kiosk.service"
echo "- Adjust screensaver timeout: Edit IDLE_TIME in /home/volumio/.xinitrc"
echo ""
if [[ "$audio_choice" == "2" ]]; then
  echo "After reboot, select 'IQaudIO Pi-DigiAMP+' as your Output Device in Volumio's Playback Options."
  echo ""
fi

read -p "Press Enter to reboot your Raspberry Pi and complete the setup..."
sudo reboot