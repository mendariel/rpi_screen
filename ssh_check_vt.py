import paramiko
import time

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

for attempt in range(5):
    try:
        ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=10)
        print("Connected!")
        break
    except Exception as e:
        print(f"Attempt {attempt+1}: {e}")
        time.sleep(5)

print("=" * 60)
print("POST-REBOOT CHECK")
print("=" * 60)

# Kiosk service status
print("\n--- Kiosk service status ---")
run(ssh, "systemctl status volumio-kiosk.service 2>&1 | head -25")

# Running processes
print("\n--- Running X/Chromium processes ---")
run(ssh, "ps aux | grep -E 'Xorg|chromium|startx|xinit' | grep -v grep || echo NONE_RUNNING")

# Xorg errors
print("\n--- Xorg log errors ---")
run(ssh, "grep -E '\\(EE\\)|Fatal' /var/log/Xorg.0.log 2>&1 || echo NO_ERRORS")

# Xorg log tail
print("\n--- Xorg log tail ---")
run(ssh, "tail -20 /var/log/Xorg.0.log 2>&1 || echo NO_LOG")

# Journal
print("\n--- Journal for kiosk (last 20) ---")
run(ssh, "journalctl -u volumio-kiosk.service --no-pager -n 20 2>&1")

# VT check
print("\n--- getty@tty1 status ---")
run(ssh, "systemctl status getty@tty1.service 2>&1 | head -5")

# 99-v3d.conf check
print("\n--- 99-v3d.conf ---")
run(ssh, "cat /etc/X11/xorg.conf.d/99-v3d.conf")

print("\nDone.")
ssh.close()
