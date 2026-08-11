# debug_admin.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'efunza_backend.settings')
sys.path.append('/home/gisbomhj/Efunza')

try:
    django.setup()
    print("✅ Django setup successful")
    
    # Check admin URL
    from django.urls import reverse
    from django.contrib.admin import site
    
    print(f"✅ Admin site registered: {site._registry.keys()}")
    
    # Try to get admin URLs
    from django.urls import get_resolver
    resolver = get_resolver()
    print(f"✅ URL resolver loaded")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()