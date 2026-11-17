import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

def backup_sqlite():
    source_db = BASE_DIR / "vrms.db"
    if not source_db.exists():
        print(f"Database file not found at {source_db}")
        return False
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = BACKUP_DIR / f"vrms_backup_{timestamp}.db"
    
    shutil.copy2(source_db, target_backup)
    print(f"[SUCCESS] Database backup created: {target_backup}")
    print(f"Size: {os.path.getsize(target_backup)} bytes")
    return True

if __name__ == "__main__":
    print("Initiating automated VRMS database backup...")
    backup_sqlite()
