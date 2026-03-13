import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.113', username='volumio', password='volumio', timeout=10)

def run(cmd, use_sudo=False):
    if use_sudo:
        cmd = f"echo volumio | sudo -S bash -c '{cmd}'"
    print(f">>> {cmd[:120]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    # Filter out the sudo password prompt from stderr
    err_lines = [l for l in err.split('\n') if l.strip() and '[sudo]' not in l]
    if err_lines:
        print(f"  STDERR: {'  '.join(err_lines)}")
    return out

print("=" * 60)
print("FIX 1: Remove 99-v3d.conf (the vc4 OutputClass culprit)")
print("=" * 60)
run("rm -f /etc/X11/xorg.conf.d/99-v3d.conf", use_sudo=True)
run("ls -la /etc/X11/xorg.conf.d/")

print("\n" + "=" * 60)
print("FIX 2: Write correct 99-tft.conf with all sections")
print("=" * 60)

# Write the complete Xorg config
xorg_config = '''Section "ServerFlags"
    Option "AutoAddDevices" "false"
    Option "AutoEnableDevices" "false"
EndSection

Section "Module"
    Disable "glamoregl"
    Disable "dri"
    Disable "dri2"
    Disable "dri3"
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
'''

# Write via a temp file to avoid quoting issues
import base64
encoded = base64.b64encode(xorg_config.encode()).decode()
run(f"echo {encoded} | base64 -d > /etc/X11/xorg.conf.d/99-tft.conf", use_sudo=True)

print("\nVerifying 99-tft.conf:")
run("cat /etc/X11/xorg.conf.d/99-tft.conf")

print("\n" + "=" * 60)
print("FIX 3: Blacklist vc4 kernel module")
print("=" * 60)
run("echo 'blacklist vc4' > /etc/modprobe.d/blacklist-vc4.conf", use_sudo=True)
run("cat /etc/modprobe.d/blacklist-vc4.conf")

print("\n" + "=" * 60)
print("FIX 4: Remove 20-noglamor.conf (forces modesetting)")
print("=" * 60)
run("rm -f /usr/share/X11/xorg.conf.d/20-noglamor.conf", use_sudo=True)
run("ls -la /usr/share/X11/xorg.conf.d/20-noglamor.conf 2>&1 || echo REMOVED")

print("\n" + "=" * 60)
print("FIX 5: Verify Xwrapper.config")
print("=" * 60)
run("cat /etc/X11/Xwrapper.config")

print("\n" + "=" * 60)
print("FIX 6: Verify kiosk service exists and is enabled")
print("=" * 60)
run("systemctl is-enabled volumio-kiosk.service 2>&1 || echo NOT_ENABLED")

print("\n" + "=" * 60)
print("ALL FIXES APPLIED - List final config files")
print("=" * 60)
run("ls -la /etc/X11/xorg.conf.d/")
run("ls -la /usr/share/X11/xorg.conf.d/")

print("\n" + "=" * 60)
print("REBOOTING PI...")
print("=" * 60)
try:
    run("reboot", use_sudo=True)
except:
    pass

ssh.close()
print("\nDone! Pi is rebooting. Wait ~30 seconds and check the TFT screen.")
