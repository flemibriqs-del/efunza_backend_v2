# check_static_files.py
import os

static_root = '/home/gisbomhj/Efunza/staticfiles'

print("=" * 60)
print("🔍 CHECKING STATIC FILES")
print("=" * 60)

if not os.path.exists(static_root):
    print(f"❌ Static root does NOT exist: {static_root}")
    print("   Run collectstatic first!")
else:
    print(f"✅ Static root exists: {static_root}")
    
    # Check admin CSS
    admin_css = os.path.join(static_root, 'admin', 'css', 'base.css')
    if os.path.exists(admin_css):
        print(f"✅ Admin CSS exists: {admin_css}")
        print(f"   Size: {os.path.getsize(admin_css)} bytes")
    else:
        print(f"❌ Admin CSS NOT found: {admin_css}")
    
    # Check admin JS
    admin_js = os.path.join(static_root, 'admin', 'js', 'theme.js')
    if os.path.exists(admin_js):
        print(f"✅ Admin JS exists: {admin_js}")
    else:
        print(f"❌ Admin JS NOT found: {admin_js}")
    
    # List static root contents
    print(f"\n📂 Static root contents ({static_root}):")
    items = os.listdir(static_root)
    for item in sorted(items):
        item_path = os.path.join(static_root, item)
        if os.path.isdir(item_path):
            sub_items = len(os.listdir(item_path))
            print(f"   📁 {item}/ ({sub_items} items)")
        else:
            size = os.path.getsize(item_path)
            print(f"   📄 {item} ({size} bytes)")

print("=" * 60)