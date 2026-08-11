# check_whitenoise.py
import sys
import subprocess

print("=" * 60)
print("🔍 CHECKING WHITENOISE")
print("=" * 60)

# Check if whitenoise is installed
try:
    import whitenoise
    print("✅ Whitenoise is installed")
    
    # Try to get version safely
    try:
        version = whitenoise.__version__
        print(f"   Version: {version}")
    except AttributeError:
        print("   Version: (unknown - but installed)")
        
except ImportError:
    print("❌ Whitenoise NOT installed")
    print("\n📦 Installing Whitenoise...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "whitenoise"])
        print("✅ Whitenoise installed successfully!")
    except Exception as e:
        print(f"❌ Failed to install: {e}")

print("=" * 60)