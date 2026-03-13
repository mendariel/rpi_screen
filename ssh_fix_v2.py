import paramiko
import base64

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.113', username='volumio', password='volumio', timeout=10)

def run_sudo(cmd):
    """Run command with sudo using stdin for password"""
    full_cmd = f"sudo -S {cmd}"
    print(f">>> sudo {cmd[:100]}")
    stdin, stdout, stderr = ssh.exec_command(full_cmd)
    stdin.write("volumio\n")
    stdin.flush()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    err_lines = [l for l in err.split('\n') if l.strip() and '[sudo]' not in l and 'password' not in l.lower()]
    if err_lines:
        print(f"  STDERR: {'  '.join(err_lines)}")
    return out

def run(cmd):
    print(f">>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    return out

# Remount root as rw
print("=" * 60)
print("Remounting filesystem as read-write")
print("=" * 60)
run_sudo("mount -o remount,rw /")

# FIX 1: Write blacklist-vc4.conf using base64 to avoid quoting issues
print("\n" + "=" * 60)
print("FIX 1: Blacklist vc4 kernel module")
print("=" * 60)
blacklist_content = "blacklist vc4\nblacklist drm_display_helper\n"
encoded = base64.b64encode(blacklist_content.encode()).decode()
run_sudo(f"bash -c 'echo {encoded} | base64 -d > /etc/modprobe.d/blacklist-vc4.conf'")
print("Verifying:")
run("cat /etc/modprobe.d/blacklist-vc4.conf")

# FIX 2: Update 99-tft.conf with AutoAddGPU false
print("\n" + "=" * 60)
print("FIX 2: Update Xorg config with AutoAddGPU false")
print("=" * 60)
xorg_config = """Section "ServerFlags"
    Option "AutoAddDevices" "false"
    Option "AutoEnableDevices" "false"
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
encoded = base64.b64encode(xorg_config.encode()).decode()
run_sudo(f"bash -c 'echo {encoded} | base64 -d > /etc/X11/xorg.conf.d/99-tft.conf'")
print("Verifying:")
run("cat /etc/X11/xorg.conf.d/99-tft.conf")

# FIX 3: Also check and remove 00-glamor.conf if it references modesetting
print("\n" + "=" * 60)
print("FIX 3: Check 00-glamor.conf")
print("=" * 60)
run("cat /usr/share/X11/xorg.conf.d/00-glamor.conf 2>/dev/null || echo NOT_FOUND")

# FIX 4: Remove 00-glamor.conf to prevent glamor from loading modesetting
print("Removing 00-glamor.conf...")
run_sudo("rm -f /usr/share/X11/xorg.conf.d/00-glamor.conf")

# Verify all configs
print("\n" + "=" * 60)
print("FINAL STATE")
print("=" * 60)
run("ls -la /etc/X11/xorg.conf.d/")
run("ls -la /usr/share/X11/xorg.conf.d/")
run("cat /etc/modprobe.d/blacklist-vc4.conf")

# Reboot
print("\n" + "=" * 60)
print("REBOOTING...")
print("=" * 60)
try:
    run_sudo("reboot")
except:
    pass

ssh.close()
print("\nPi is rebooting. Wait ~40 seconds...")
