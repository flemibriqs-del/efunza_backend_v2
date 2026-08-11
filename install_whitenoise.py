# install_whitenoise.py
import sys
import subprocess

print("=" * 60)
print("📦 Installing Whitenoise...")
print("=" * 60)

try:
    subprocess.check_call([
        sys.executable,
        '-m',
        'pip',
        'install',
        'whitenoise'
    ])
    print("✅ Whitenoise installed successfully!")
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 60)