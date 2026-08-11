# install_sentry.py
import subprocess
import sys
import os

print("=" * 60)
print("📦 Installing Sentry SDK...")
print("=" * 60)

try:
    # Install sentry-sdk
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "pip", 
        "install", 
        "sentry-sdk"
    ])
    print("\n✅ Sentry SDK installed successfully!")
    
    # Verify installation
    try:
        import sentry_sdk
        print(f"✅ Sentry SDK version: {sentry_sdk.__version__}")
    except ImportError:
        print("❌ Sentry SDK not found after installation")
        
except Exception as e:
    print(f"\n❌ Installation failed: {e}")

print("\n" + "=" * 60)