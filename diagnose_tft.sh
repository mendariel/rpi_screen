#!/bin/bash
# TFT Kiosk Diagnostic Script
# Run via SSH: bash diagnose_tft.sh 2>&1 | tee /tmp/tft_diag.txt

echo "============================================"
echo "TFT Kiosk Diagnostic Report"
echo "Date: $(date)"
echo "============================================"
echo ""

echo "=== Volumio Version ==="
cat /volumio/app/package.json 2>/dev/null | grep '"version"' | head -1 || echo "Not found"
cat /etc/os-release | grep PRETTY_NAME || true
echo ""

echo "=== Framebuffers ==="
ls -la /dev/fb* 2>/dev/null || echo "No framebuffers found!"
echo ""

echo "=== Kiosk Service Status ==="
systemctl status volumio-kiosk.service --no-pager -l 2>&1 || echo "Service not found"
echo ""

echo "=== Kiosk Service File ==="
cat /etc/systemd/system/volumio-kiosk.service 2>/dev/null || echo "Service file not found"
echo ""

echo "=== .xinitrc ==="
cat /home/volumio/.xinitrc 2>/dev/null || echo ".xinitrc not found"
echo ""

echo "=== Xorg Config ==="
cat /etc/X11/xorg.conf.d/99-tft.conf 2>/dev/null || echo "99-tft.conf not found"
echo ""

echo "=== Xorg Log (last 30 lines) ==="
cat /home/volumio/.local/share/xorg/Xorg.0.log 2>/dev/null | tail -30 \
  || cat /var/log/Xorg.0.log 2>/dev/null | tail -30 \
  || echo "No Xorg log found"
echo ""

echo "=== Installed Key Packages ==="
for pkg in xserver-xorg xserver-xorg-video-fbdev xinit chromium chromium-browser x11-xserver-utils xprintidle xdotool unclutter python3-tk curl; do
  dpkg -l "$pkg" 2>/dev/null | grep -E "^ii" | awk '{print $1, $2, $3}' || echo "NOT INSTALLED: $pkg"
done
echo ""

echo "=== startx location ==="
which startx 2>/dev/null || echo "startx not found in PATH"
which chromium 2>/dev/null || echo "chromium not found"
which chromium-browser 2>/dev/null || echo "chromium-browser not found"
echo ""

echo "=== Current VT ==="
fgconsole 2>/dev/null || cat /sys/class/tty/tty0/active 2>/dev/null || echo "Cannot determine VT"
echo ""

echo "=== Systemd Journal for kiosk (last 50 lines) ==="
journalctl -u volumio-kiosk.service -n 50 --no-pager 2>&1 || echo "No journal entries"
echo ""

echo "=== Boot Config (TFT overlays) ==="
grep -E "piscreen|ads7846|fbdev|fb1" /boot/userconfig.txt 2>/dev/null || echo "/boot/userconfig.txt missing or no TFT entries"
grep -E "piscreen|ads7846|fbdev|fb1" /boot/config.txt 2>/dev/null | head -20 || true
echo ""

echo "=== volumio user info ==="
id volumio 2>/dev/null || echo "volumio user not found"
groups volumio 2>/dev/null || true
echo ""

echo "=== /tmp/startx_error.log ==="
cat /tmp/startx_error.log 2>/dev/null || echo "No startx error log"
echo ""

echo "============================================"
echo "Diagnostic complete."
echo "If saved to file: cat /tmp/tft_diag.txt"
echo "============================================"
