import paramiko
import time

for attempt in range(5):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('192.168.1.113', username='volumio', password='volumio', timeout=10)
        print("Connected!")
        break
    except Exception as e:
        print(f"Attempt {attempt+1}: {e}")
        time.sleep(5)
else:
    print("Could not connect after 5 attempts")
    exit(1)

def run(cmd):
    print(f">>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    err_lines = [l for l in err.split('\n') if l.strip() and '[sudo]' not in l]
    if err_lines:
        print(f"  STDERR: {'  '.join(err_lines)}")
    return out

print("=" * 60)
print("POST-REBOOT DIAGNOSTICS")
print("=" * 60)

print("\n--- Kiosk service status ---")
run("systemctl status volumio-kiosk.service 2>&1 | head -30")

print("\n--- Xorg log errors ---")
run("grep -E '\\(EE\\)|Fatal' /var/log/Xorg.0.log 2>&1 || echo NO_ERRORS")

print("\n--- Xorg log tail ---")
run("tail -30 /var/log/Xorg.0.log 2>&1 || echo NO_LOG")

print("\n--- vc4 module loaded? ---")
run("lsmod | grep vc4 || echo NOT_LOADED")

print("\n--- DRI devices? ---")
run("ls -la /dev/dri/ 2>&1 || echo NO_DRI")

print("\n--- Running X processes ---")
run("ps aux | grep -E 'Xorg|chromium|startx|xinit' | grep -v grep || echo NONE_RUNNING")

print("\n--- Journal for kiosk ---")
run("journalctl -u volumio-kiosk.service --no-pager -n 30 2>&1")

ssh.close()
print("\nDone.")
