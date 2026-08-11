# backup.py - Database backup script for cPanel
import os
import shutil
import datetime
import glob
import time
import sys

print("=" * 60)
print("🔄 Starting Database Backup...")
print("=" * 60)

# Define paths
PROJECT_DIR = '/home/gisbomhj/Efunza'
BACKUP_DIR = '/home/gisbomhj/backups'
SOURCE_DB = os.path.join(PROJECT_DIR, 'db.sqlite3')

# Create backup directory if it doesn't exist
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"✅ Backup directory: {BACKUP_DIR}")
except Exception as e:
    print(f"❌ Failed to create backup directory: {e}")
    sys.exit(1)

# Check if database exists
if not os.path.exists(SOURCE_DB):
    print(f"❌ Database not found: {SOURCE_DB}")
    sys.exit(1)

# Get database size
db_size = os.path.getsize(SOURCE_DB) / (1024 * 1024)
print(f"📦 Database size: {db_size:.2f} MB")

# Create backup with timestamp
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = os.path.join(BACKUP_DIR, f'db_backup_{timestamp}.sqlite3')

try:
    # Copy database
    shutil.copy2(SOURCE_DB, backup_file)
    backup_size = os.path.getsize(backup_file) / (1024 * 1024)
    print(f"✅ Backup created: {os.path.basename(backup_file)}")
    print(f"📦 Backup size: {backup_size:.2f} MB")
    
    # Clean up old backups - keep last 14 days
    backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, 'db_backup_*.sqlite3')))
    deleted_count = 0
    
    # Delete backups older than 14 days
    for f in backup_files:
        file_age = time.time() - os.path.getctime(f)
        if file_age > 14 * 24 * 3600:  # 14 days in seconds
            os.remove(f)
            deleted_count += 1
            print(f"🗑️ Removed old backup: {os.path.basename(f)}")
    
    # Keep only last 10 backups (safety)
    backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, 'db_backup_*.sqlite3')))
    if len(backup_files) > 10:
        for f in backup_files[:-10]:
            os.remove(f)
            deleted_count += 1
            print(f"🗑️ Removed extra backup: {os.path.basename(f)}")
    
    if deleted_count > 0:
        print(f"✅ Deleted {deleted_count} old backup(s)")
    
    # List current backups
    backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, 'db_backup_*.sqlite3')))
    total_size = sum(os.path.getsize(f) for f in backup_files) / (1024 * 1024)
    print(f"\n📊 Total backups: {len(backup_files)}")
    print(f"📦 Total size: {total_size:.2f} MB")
    
except Exception as e:
    print(f"❌ Backup failed: {e}")
    sys.exit(1)

print("=" * 60)
print("✅ Backup completed successfully!")
print(f"📁 Location: {BACKUP_DIR}")
print("=" * 60)