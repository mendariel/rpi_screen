import paramiko
import base64

PI_HOST = "192.168.1.113"
PI_USER = "volumio"
PI_PASS = "volumio"

def run(ssh, cmd):
    print(f">>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip():
        print(out.strip())
    if err.strip():
        print(f"STDERR: {err.strip()}")
    return out.strip()

def write_file_b64(ssh, path, content):
    """Write file content using base64 to avoid shell escaping issues."""
    b64 = base64.b64encode(content.encode()).decode()
    run(ssh, f"echo '{b64}' | base64 -d | sudo tee {path} > /dev/null")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=10)
print("Connected!")

print("=" * 60)
print("FIX: VT SWITCHING ISSUE")
print("=" * 60)

# Fix 1: Disable getty on tty1 so it doesn't hold the VT
print("\n=== Disabling getty@tty1 ===")
run(ssh, "sudo systemctl stop getty@tty1")
run(ssh, "sudo systemctl disable getty@tty1")
run(ssh, "sudo systemctl mask getty@tty1")  # mask prevents re-enabling

# Fix 2: Update kiosk service with TTY settings and -keeptty
kiosk_service = """[Unit]
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
UtterlyUseATTY=yes
ExecStartPre=/bin/sleep 15
ExecStart=/usr/bin/startx /home/volumio/.xinitrc -- :0 vt1 -keeptty
User=volumio
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

print("\n=== Updating kiosk service ===")
write_file_b64(ssh, "/etc/systemd/system/volumio-kiosk.service", kiosk_service)
print("Verifying:")
run(ssh, "cat /etc/systemd/system/volumio-kiosk.service")

# Reload systemd
run(ssh, "sudo systemctl daemon-reload")

# Fix 3: Also re-overwrite 99-v3d.conf (SquashFS restored it)
# Actually, the Xorg log showed ServerLayout works even WITH it, 
# but let's also add a Module section to not load modesetting just in case.
# Actually, let's leave 99-v3d.conf alone since the ServerLayout approach works.

# Fix 4: Enable input devices - we need at least the touchscreen
# Change AutoAddDevices to true, but keep AutoAddGPU false
xorg_conf = """Section "ServerFlags"
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
    Identifier "TFT Layout"
    Screen "TFT"
EndSection
"""

print("\n=== Updating 99-tft.conf (re-enable input auto-add) ===")
write_file_b64(ssh, "/etc/X11/xorg.conf.d/99-tft.conf", xorg_conf)
print("Verifying:")
run(ssh, "cat /etc/X11/xorg.conf.d/99-tft.conf")

# Show final state
print("\n=== Final state ===")
run(ssh, "systemctl is-enabled volumio-kiosk.service")
run(ssh, "systemctl is-enabled getty@tty1.service 2>&1 || echo masked")
run(ssh, "ls -la /etc/X11/xorg.conf.d/")

# Reboot
print("\n=== Rebooting ===")
try:
    ssh.exec_command("sudo reboot", timeout=5)
except:
    pass

print("Rebooting... wait ~50 seconds then run the check script")
ssh.close()
