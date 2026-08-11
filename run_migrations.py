# run_migrations.py
import os
import sys
import django
from django.core.management import call_command

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'efunza_backend.settings')
sys.path.append('/home/gisbomhj/Efunza')

# Initialize Django
django.setup()

print("=" * 60)
print("Running Django Migrations...")
print("=" * 60)

try:
    # Create migration files
    print("\n📝 Creating migration files...")
    call_command('makemigrations')
    print("✅ Migration files created successfully!")
    
    # Apply migrations
    print("\n🔄 Applying migrations to database...")
    call_command('migrate')
    print("✅ Migrations applied successfully!")
    
    print("\n" + "=" * 60)
    print("✅ All migrations completed successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("=" * 60)