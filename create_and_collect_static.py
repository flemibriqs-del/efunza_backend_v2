# create_and_collect_static.py
import os
import sys
import subprocess
import shutil

print("=" * 60)
print("📦 CREATING AND COLLECTING STATIC FILES")
print("=" * 60)

project_dir = '/home/gisbomhj/Efunza'
static_root = os.path.join(project_dir, 'staticfiles')
manage_py = os.path.join(project_dir, 'manage.py')

# Step 1: Create static directory
print("\n📁 Creating static directory...")
try:
    os.makedirs(static_root, exist_ok=True)
    print(f"✅ Created: {static_root}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Step 2: Run collectstatic
print("\n📦 Running collectstatic...")
try:
    result = subprocess.run([
        sys.executable,
        manage_py,
        'collectstatic',
        '--noinput',
        '--clear',
        '--verbosity',
        '2'
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

# Step 3: Verify
print("\n🔍 Verifying static files...")
admin_css = os.path.join(static_root, 'admin', 'css', 'base.css')
admin_js = os.path.join(static_root, 'admin', 'js', 'theme.js')

if os.path.exists(admin_css):
    print(f"✅ Admin CSS found: {admin_css}")
    print(f"   Size: {os.path.getsize(admin_css)} bytes")
else:
    print(f"❌ Admin CSS NOT found")

if os.path.exists(admin_js):
    print(f"✅ Admin JS found: {admin_js}")
else:
    print(f"❌ Admin JS NOT found")

# Step 4: Create a test file
print("\n📝 Creating test HTML file...")
test_file = os.path.join(static_root, 'test.html')
try:
    with open(test_file, 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head><title>Static Test</title></head>
<body>
    <h1 style="color: green;">✅ Static files are working!</h1>
    <p>If you can see this, static files are being served correctly.</p>
    <p>Time: """ + str(__import__('datetime').datetime.now()) + """</p>
</body>
</html>
""")
    print(f"✅ Created test file: {test_file}")
except Exception as e:
    print(f"⚠️ Error creating test file: {e}")

# Step 5: List contents
print("\n📂 Static root contents:")
if os.path.exists(static_root):
    items = os.listdir(static_root)
    print(f"   Total: {len(items)} items")
    for item in sorted(items)[:15]:
        item_path = os.path.join(static_root, item)
        if os.path.isdir(item_path):
            sub_items = len(os.listdir(item_path))
            print(f"   📁 {item}/ ({sub_items} items)")
        else:
            size = os.path.getsize(item_path)
            print(f"   📄 {item} ({size} bytes)")

print("\n" + "=" * 60)
print("✅ Static files created and collected!")
print("\n📝 Test URLs:")
print("1. https://efunza.jamelecinnovations.com/static/test.html")
print("2. https://efunza.jamelecinnovations.com/static/admin/css/base.css")
print("\n📝 Next steps:")
print("1. Restart your Django app in cPanel")
print("2. Clear browser cache (Ctrl+Shift+Delete)")
print("3. Refresh admin panel")
print("4. If still not working, check cPanel static files configuration")
print("=" * 60)