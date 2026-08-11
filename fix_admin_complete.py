# fix_admin_complete.py
import os
import sys
import subprocess
import shutil

print("=" * 60)
print("🔧 COMPLETE ADMIN STATIC FIX")
print("=" * 60)

project_dir = '/home/gisbomhj/Efunza'
static_root = os.path.join(project_dir, 'staticfiles')
manage_py = os.path.join(project_dir, 'manage.py')

# Step 1: Remove old static files
print("\n🗑️ Removing old static files...")
try:
    if os.path.exists(static_root):
        shutil.rmtree(static_root)
        print("✅ Removed old static directory")
except Exception as e:
    print(f"⚠️ Could not remove: {e}")

# Step 2: Collect static files
print("\n📦 Collecting static files...")
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

# Step 3: Verify files
print("\n🔍 Verifying static files...")
admin_css = os.path.join(static_root, 'admin', 'css', 'base.css')
admin_js = os.path.join(static_root, 'admin', 'js', 'theme.js')

if os.path.exists(admin_css):
    print(f"✅ Admin CSS found")
else:
    print(f"❌ Admin CSS NOT found")

if os.path.exists(admin_js):
    print(f"✅ Admin JS found")
else:
    print(f"❌ Admin JS NOT found")

# Step 4: Create a simple favicon if not exists
favicon_path = os.path.join(static_root, 'favicon.ico')
if not os.path.exists(favicon_path):
    print("\n📝 Creating favicon...")
    try:
        # Create a simple 1x1 transparent icon
        with open(favicon_path, 'wb') as f:
            # Simple 1x1 transparent GIF
            f.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
        print(f"✅ Favicon created at: {favicon_path}")
    except Exception as e:
        print(f"⚠️ Could not create favicon: {e}")

print("\n" + "=" * 60)
print("✅ Fix completed!")
print("\n📝 Next steps:")
print("1. Restart your Django app in cPanel")
print("2. Clear browser cache (Ctrl+Shift+Delete)")
print("3. Hard refresh admin panel (Ctrl+Shift+R)")
print("4. Try accessing: https://efunza.jamelecinnovations.com/admin/")
print("=" * 60)