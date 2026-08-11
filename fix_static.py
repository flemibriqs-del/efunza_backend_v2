# fix_static.py
import os
import sys
import subprocess
import shutil

print("=" * 60)
print("🔧 FIXING STATIC FILES")
print("=" * 60)

project_dir = '/home/gisbomhj/Efunza'
static_root = os.path.join(project_dir, 'staticfiles')

# Step 1: Remove old static files
print("\n🗑️ Removing old static files...")
if os.path.exists(static_root):
    try:
        shutil.rmtree(static_root)
        print("✅ Removed old static directory")
    except Exception as e:
        print(f"⚠️ Could not remove: {e}")

# Step 2: Collect static files
print("\n📦 Collecting static files...")
try:
    subprocess.check_call([
        sys.executable,
        os.path.join(project_dir, 'manage.py'),
        'collectstatic',
        '--noinput',
        '--clear'
    ], cwd=project_dir)
    print("✅ Static files collected successfully!")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 3: Verify
print("\n🔍 Verifying static files...")
admin_css = os.path.join(static_root, 'admin', 'css', 'base.css')
if os.path.exists(admin_css):
    print(f"✅ Admin CSS found: {admin_css}")
else:
    print(f"❌ Admin CSS NOT found: {admin_css}")

print("\n" + "=" * 60)
print("✅ Done! Restart your app and refresh the admin panel.")
print("=" * 60)