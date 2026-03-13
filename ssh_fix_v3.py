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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=10)
print("Connected!")

# Strategy: Instead of deleting 99-v3d.conf (SquashFS restores it),
# OVERWRITE it with harmless content. The overlay will persist our version.

# 1. Overwrite 99-v3d.conf with a harmless empty config (just a comment)
v3d_content = """# Overridden - original vc4 OutputClass disabled for TFT kiosk mode
# (Do not delete this file - SquashFS will restore the original)
"""
v3d_b64 = base64.b64encode(v3d_content.encode()).decode()
print("\n=== Overwriting 99-v3d.conf with harmless content ===")
run(ssh, f"echo '{v3d_b64}' | base64 -d | sudo tee /etc/X11/xorg.conf.d/99-v3d.conf > /dev/null")
run(ssh, "cat /etc/X11/xorg.conf.d/99-v3d.conf")

# 2. Overwrite 20-noglamor.conf with harmless content
noglamor_content = """# Overridden - original modesetting config disabled for TFT kiosk mode
"""
noglamor_b64 = base64.b64encode(noglamor_content.encode()).decode()
print("\n=== Overwriting 20-noglamor.conf with harmless content ===")
run(ssh, f"echo '{noglamor_b64}' | base64 -d | sudo tee /usr/share/X11/xorg.conf.d/20-noglamor.conf > /dev/null")
run(ssh, "cat /usr/share/X11/xorg.conf.d/20-noglamor.conf")

# 3. Also check if there's a 00-glamor.conf that came back
print("\n=== Checking for 00-glamor.conf ===")
run(ssh, "ls -la /usr/share/X11/xorg.conf.d/")

# 4. If 00-glamor.conf exists, overwrite it too
glamor_content = """# Overridden - disabled for TFT kiosk mode
"""
glamor_b64 = base64.b64encode(glamor_content.encode()).decode()
run(ssh, f"echo '{glamor_b64}' | base64 -d | sudo tee /usr/share/X11/xorg.conf.d/00-glamor.conf > /dev/null")

# 5. Verify our 99-tft.conf is still there and correct
print("\n=== Current 99-tft.conf ===")
run(ssh, "cat /etc/X11/xorg.conf.d/99-tft.conf")

# 6. List all xorg config files
print("\n=== All xorg.conf.d files ===")
run(ssh, "ls -la /etc/X11/xorg.conf.d/")
run(ssh, "ls -la /usr/share/X11/xorg.conf.d/")

# 7. Reboot
print("\n=== Rebooting ===")
try:
    ssh.exec_command("sudo reboot", timeout=5)
except:
    pass

print("Rebooting... wait ~45 seconds then run ssh_check_reboot.py")
ssh.close()
