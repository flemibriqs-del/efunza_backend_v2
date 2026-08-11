# debug_admin_500.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'efunza_backend.settings')
sys.path.append('/home/gisbomhj/Efunza')

print("=" * 60)
print("🔍 DEBUGGING ADMIN 500 ERROR")
print("=" * 60)

try:
    django.setup()
    print("✅ Django setup successful")
    
    # Check admin
    from django.contrib import admin
    from django.contrib.admin import site
    
    print(f"✅ Admin site loaded")
    print(f"✅ Registered models: {len(site._registry)}")
    
    # Try to get admin URLs
    from django.urls import get_resolver
    resolver = get_resolver()
    
    # Check if admin is in URLs
    from django.urls import reverse
    try:
        admin_url = reverse('admin:index')
        print(f"✅ Admin URL: {admin_url}")
    except Exception as e:
        print(f"⚠️ Admin URL error: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)