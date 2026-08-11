# fix_admin_styling.py
import os
import sys
import subprocess
import shutil

print("=" * 60)
print("🎨 FIXING ADMIN STYLING")
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
    else:
        print("ℹ️ No static directory found")
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

# Step 3: Verify static files
print("\n🔍 Verifying static files...")
admin_css = os.path.join(static_root, 'admin', 'css', 'base.css')
admin_js = os.path.join(static_root, 'admin', 'js', 'theme.js')

if os.path.exists(admin_css):
    print(f"✅ Admin CSS found: {admin_css}")
    print(f"   Size: {os.path.getsize(admin_css)} bytes")
else:
    print(f"❌ Admin CSS NOT found: {admin_css}")

if os.path.exists(admin_js):
    print(f"✅ Admin JS found: {admin_js}")
else:
    print(f"❌ Admin JS NOT found: {admin_js}")

# Step 4: List static directory contents
print("\n📂 Static directory contents:")
if os.path.exists(static_root):
    items = os.listdir(static_root)
    print(f"   Total items: {len(items)}")
    for item in sorted(items)[:10]:
        item_path = os.path.join(static_root, item)
        if os.path.isdir(item_path):
            print(f"   📁 {item}/")
        else:
            print(f"   📄 {item}")
else:
    print("   ❌ Static root not found!")

print("\n" + "=" * 60)
print("✅ Fix completed!")
print("\n📝 Next steps:")
print("1. Restart your Django app in cPanel")
print("2. Clear browser cache (Ctrl+Shift+Delete)")
print("3. Hard refresh admin panel (Ctrl+Shift+R)")
print("4. Check: https://efunza.jamelecinnovations.com/static/admin/css/base.css")
print("=" * 60)