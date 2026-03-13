import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

for attempt in range(5):
    try:
        ssh.connect('192.168.1.113', username='volumio', password='volumio', timeout=10)
        print('Connected to Pi.')
        break
    except Exception as e:
        print(f'Attempt {attempt+1}: {e}')
        time.sleep(10)
else:
    print('FAILED to connect after 5 attempts')
    exit(1)

checks = [
    ('Kiosk service status', 'systemctl status volumio-kiosk.service --no-pager -l'),
    ('Xorg process', 'pgrep -a Xorg'),
    ('Chromium processes', 'pgrep -a chromium | head -5'),
    ('unclutter process', 'pgrep -a unclutter'),
    ('99-tft.conf', 'cat /etc/X11/xorg.conf.d/99-tft.conf'),
    ('99-v3d.conf (should be harmless comment)', 'cat /etc/X11/xorg.conf.d/99-v3d.conf'),
    ('20-noglamor.conf (should be harmless comment)', 'cat /usr/share/X11/xorg.conf.d/20-noglamor.conf'),
    ('getty@tty1 (should be masked)', 'systemctl status getty@tty1 --no-pager 2>&1 || true'),
    ('Framebuffer device', 'ls -la /dev/fb*'),
    ('Touchscreen input', 'ls -la /dev/input/event*'),
    ('Xorg errors (EE lines)', 'grep "\\(EE\\)" /var/log/Xorg.0.log 2>/dev/null || echo "No EE errors found"'),
    ('Uptime', 'uptime'),
]

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for label, cmd in checks:
    print(f'\n===== {label} =====')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print(f'STDERR: {err}')
    if not out and not err:
        print('(no output)')

ssh.close()
print('\n===== VALIDATION COMPLETE =====')
