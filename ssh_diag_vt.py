import paramiko

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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

for attempt in range(3):
    try:
        ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=10)
        print("Connected!")
        break
    except Exception as e:
        print(f"Attempt {attempt+1}: {e}")
        import time; time.sleep(5)

print("=" * 60)
print("VT SWITCH DIAGNOSTICS")
print("=" * 60)

# Full Xorg log
print("\n--- Full Xorg log ---")
run(ssh, "cat /var/log/Xorg.0.log 2>&1")

# Check what VTs are in use
print("\n--- VT status ---")
run(ssh, "fgconsole 2>&1 || echo 'fgconsole failed'")
run(ssh, "cat /sys/class/tty/tty0/active 2>&1 || echo 'no active tty'")
run(ssh, "who 2>&1")

# Check Xwrapper.config
print("\n--- Xwrapper.config ---")
run(ssh, "cat /etc/X11/Xwrapper.config 2>&1")

# Check the kiosk service definition
print("\n--- Kiosk service ---")
run(ssh, "cat /etc/systemd/system/volumio-kiosk.service 2>&1")

# Check .xinitrc
print("\n--- .xinitrc ---")
run(ssh, "cat /home/volumio/.xinitrc 2>&1")

# Check if getty or agetty is using vt1
print("\n--- Processes on tty/vt ---")
run(ssh, "ps aux | grep -E 'getty|tty|console' | grep -v grep 2>&1")

# Check systemd for default getty services
print("\n--- Getty/console services ---")
run(ssh, "systemctl list-units '*getty*' '*console*' 2>&1")

# Check 99-v3d.conf and 20-noglamor.conf survived the reboot
print("\n--- 99-v3d.conf content after reboot ---")
run(ssh, "cat /etc/X11/xorg.conf.d/99-v3d.conf 2>&1")

print("\n--- 20-noglamor.conf content after reboot ---")
run(ssh, "cat /usr/share/X11/xorg.conf.d/20-noglamor.conf 2>&1")

# Check if vc4 loaded (should still load, but modesetting won't be assigned)
print("\n--- vc4 module ---")
run(ssh, "lsmod | grep vc4 || echo NOT_LOADED")

# Check DRI devices
print("\n--- DRI devices ---")
run(ssh, "ls -la /dev/dri/ 2>&1 || echo NO_DRI")

print("\nDone.")
ssh.close()
