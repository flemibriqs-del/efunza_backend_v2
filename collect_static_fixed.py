# collect_static_fixed.py
import os
import sys
import subprocess
import shutil

print("=" * 60)
print("📦 COLLECTING STATIC FILES")
print("=" * 60)

project_dir = '/home/gisbomhj/Efunza'
static_root = os.path.join(project_dir, 'staticfiles')
manage_py = os.path.join(project_dir, 'manage.py')

# Remove old static files
print("\n🗑️ Removing old static files...")
if os.path.exists(static_root):
    try:
        shutil.rmtree(static_root)
        print("✅ Removed old static directory")
    except Exception as e:
        print(f"⚠️ Could not remove: {e}")

# Collect static files
print("\n📦 Running collectstatic...")
try:
    result = subprocess.run([
        sys.executable,
        manage_py,
        'collectstatic',
        '--noinput',
        '--clear'
    ], cwd=project_dir, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    if result.returncode == 0:
        print("✅ Static files collected successfully!")
    else:
        print(f"❌ Error code: {result.returncode}")
except Exception as e:
    print(f"❌ Error: {e}")

# Verify
print("\n🔍 Verifying static files...")
admin_css = os.path.join(static_root, 'admin', 'css', 'base.css')
if os.path.exists(admin_css):
    print(f"✅ Admin CSS found!")
else:
    print(f"❌ Admin CSS NOT found")

print("\n" + "=" * 60)
print("✅ Done!")
print("=" * 60)