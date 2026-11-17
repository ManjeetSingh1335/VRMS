#!/bin/bash
# VRMS Automated Database Backup Script (Linux/Docker/PostgreSQL/SQLite)
set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgres* ]]; then
    echo "[INFO] Performing PostgreSQL backup via pg_dump..."
    pg_dump "$DATABASE_URL" > "$BACKUP_DIR/vrms_postgres_backup_${TIMESTAMP}.sql"
    echo "[SUCCESS] PostgreSQL dump created at $BACKUP_DIR/vrms_postgres_backup_${TIMESTAMP}.sql"
else
    echo "[INFO] Performing SQLite database file backup..."
    if [ -f "./vrms.db" ]; then
        cp ./vrms.db "$BACKUP_DIR/vrms_backup_${TIMESTAMP}.db"
        echo "[SUCCESS] SQLite backup created at $BACKUP_DIR/vrms_backup_${TIMESTAMP}.db"
    else
        echo "[WARNING] vrms.db not found. Trying Python backup script..."
        python3 scripts/backup.py
    fi
fi
