import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.113', username='volumio', password='volumio', timeout=10)

commands = [
    'echo "=== XORG CONFIG ==="',
    'cat /etc/X11/xorg.conf.d/99-tft.conf 2>&1 || echo FILE_NOT_FOUND',
    'echo "=== XWRAPPER ==="',
    'cat /etc/X11/Xwrapper.config 2>&1 || echo FILE_NOT_FOUND',
    'echo "=== FRAMEBUFFERS ==="',
    'ls -la /dev/fb* 2>&1',
    'echo "=== DRI DEVICES ==="',
    'ls -la /dev/dri/ 2>&1 || echo NO_DRI',
    'echo "=== VC4 IN CONFIG.TXT ==="',
    'grep -i vc4 /boot/config.txt 2>&1 || echo NOT_FOUND',
    'echo "=== VC4 IN USERCONFIG ==="',
    'grep -i vc4 /boot/userconfig.txt 2>&1 || echo NOT_FOUND',
    'echo "=== BLACKLIST VC4 ==="',
    'cat /etc/modprobe.d/blacklist-vc4.conf 2>&1 || echo FILE_NOT_FOUND',
    'echo "=== LOADED VC4 MODULE ==="',
    'lsmod | grep vc4 || echo NOT_LOADED',
    'echo "=== KIOSK SERVICE STATUS ==="',
    'systemctl status volumio-kiosk.service 2>&1 | head -25',
    'echo "=== XORG LOG ERRORS ==="',
    'grep -iE "error|fatal|cannot|failed" /var/log/Xorg.0.log 2>&1 | tail -20 || echo NO_LOG',
    'echo "=== XORG LOG TAIL ==="',
    'tail -50 /var/log/Xorg.0.log 2>&1 || echo NO_LOG',
    'echo "=== XINITRC HEAD ==="',
    'head -5 /home/volumio/.xinitrc 2>&1 || echo FILE_NOT_FOUND',
]

full_cmd = ' ; '.join(commands)
stdin, stdout, stderr = ssh.exec_command(full_cmd)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err.strip():
    print("STDERR:", err)
ssh.close()
