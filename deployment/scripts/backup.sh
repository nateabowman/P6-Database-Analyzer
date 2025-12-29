#!/bin/bash
# Backup script for P6 Analyzer data

BACKUP_DIR="/backup/p6-analyzer"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

# Backup data directory
tar -czf "$BACKUP_FILE" \
    ~/.p6_analyzer/data \
    ~/.p6_analyzer/credentials \
    logs/

echo "Backup created: $BACKUP_FILE"

