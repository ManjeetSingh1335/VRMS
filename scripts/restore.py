import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"

def restore_latest_backup():
    if not BACKUP_DIR.exists():
        print("No backups directory found.")
        return False
        
    backups = sorted(BACKUP_DIR.glob("vrms_backup_*.db"), key=os.path.getmtime, reverse=True)
    if not backups:
        print("No SQLite backups found in backups folder.")
        return False
        
    latest_backup = backups[0]
    target_db = BASE_DIR / "vrms.db"
    
    shutil.copy2(latest_backup, target_db)
    print(f"[SUCCESS] Database successfully restored from: {latest_backup.name}")
    print(f"Target DB: {target_db}")
    return True

if __name__ == "__main__":
    restore_latest_backup()
