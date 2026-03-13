import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.113', username='volumio', password='volumio', timeout=10)

def run(cmd):
    print(f">>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    if err:
        print(f"  STDERR: {err}")
    return out

# Step 1: Find the vc4 OutputClass config that's auto-adding the GPU
print("=" * 60)
print("STEP 1: Find vc4 OutputClass config files")
print("=" * 60)
run("grep -rl 'vc4' /usr/share/X11/xorg.conf.d/ 2>/dev/null")
run("grep -rl 'vc4' /etc/X11/xorg.conf.d/ 2>/dev/null")
run("ls -la /usr/share/X11/xorg.conf.d/")
run("cat /usr/share/X11/xorg.conf.d/20-noglamor.conf 2>/dev/null || echo NOT_FOUND")

# Show contents of any vc4-related files
for f in [
    "/usr/share/X11/xorg.conf.d/20-noglamor.conf",
    "/usr/share/X11/xorg.conf.d/40-libinput.conf",
]:
    print(f"\n--- {f} ---")
    run(f"cat {f} 2>/dev/null || echo NOT_FOUND")

ssh.close()
print("\nDone diagnosing.")
