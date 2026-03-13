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
    exit_code = stdout.channel.recv_exit_status()
    return out, exit_code

# Step 1: Show the offending file
print("=" * 60)
print("STEP 1: Show 99-v3d.conf (the culprit)")
print("=" * 60)
run("cat /etc/X11/xorg.conf.d/99-v3d.conf")

# Step 2: Show 20-noglamor.conf
print("\n" + "=" * 60)
print("STEP 2: Show 20-noglamor.conf")
print("=" * 60)
run("cat /usr/share/X11/xorg.conf.d/20-noglamor.conf")

# Step 3: Show all files in /etc/X11/xorg.conf.d/
print("\n" + "=" * 60)
print("STEP 3: All files in /etc/X11/xorg.conf.d/")
print("=" * 60)
run("ls -la /etc/X11/xorg.conf.d/")

ssh.close()
print("\nDone.")
