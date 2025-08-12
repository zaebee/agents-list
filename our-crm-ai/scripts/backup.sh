#!/bin/bash
# AI-CRM Database Backup Script

set -e

# Configuration
BACKUP_DIR="./backups"
COMPOSE_FILE="docker-compose.phase2a.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗄️ AI-CRM Database Backup Script${NC}"
echo "================================"

# Create backup directory
mkdir -p "$BACKUP_PATH"

# Load environment variables
if [ -f ".env" ]; then
    source .env
fi

# Database backup
echo -e "${GREEN}📊 Creating database backup...${NC}"
if docker compose -f $COMPOSE_FILE exec -T postgres pg_dump -U aicrm_user aicrm_db > "$BACKUP_PATH/database.sql"; then
    echo -e "${GREEN}✅ Database backup created: $BACKUP_PATH/database.sql${NC}"
else
    echo -e "${RED}❌ Database backup failed${NC}"
    exit 1
fi

# Application data backup
echo -e "${GREEN}📁 Backing up application data...${NC}"
if [ -d "./data" ]; then
    cp -r ./data "$BACKUP_PATH/"
    echo -e "${GREEN}✅ Application data backup completed${NC}"
fi

# Configuration backup
echo -e "${GREEN}⚙️ Backing up configuration...${NC}"
cp .env "$BACKUP_PATH/.env.backup" 2>/dev/null || true
cp -r ./logs "$BACKUP_PATH/" 2>/dev/null || true

# Create backup summary
cat > "$BACKUP_PATH/backup_info.txt" << EOF
AI-CRM Backup Information
========================
Backup Date: $(date)
Backup Path: $BACKUP_PATH
Database: aicrm_db
Backup Size: $(du -sh "$BACKUP_PATH" | cut -f1)

Files Included:
- database.sql (PostgreSQL dump)
- data/ (application data)
- logs/ (application logs)
- .env.backup (environment configuration)

Restore Instructions:
1. Stop the application: docker compose -f $COMPOSE_FILE down
2. Restore database: docker compose -f $COMPOSE_FILE exec -T postgres psql -U aicrm_user aicrm_db < $BACKUP_PATH/database.sql
3. Restore data: cp -r $BACKUP_PATH/data ./
4. Start application: docker compose -f $COMPOSE_FILE up -d
EOF

# Compress backup
echo -e "${GREEN}🗜️ Compressing backup...${NC}"
tar -czf "$BACKUP_DIR/aicrm_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "backup_$TIMESTAMP"

# Cleanup uncompressed backup
rm -rf "$BACKUP_PATH"

# Show summary
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/aicrm_backup_$TIMESTAMP.tar.gz" | cut -f1)
echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo "📦 Backup file: $BACKUP_DIR/aicrm_backup_$TIMESTAMP.tar.gz"
echo "📏 Backup size: $BACKUP_SIZE"

# Cleanup old backups (keep last 7 days)
echo -e "${YELLOW}🧹 Cleaning up old backups...${NC}"
find "$BACKUP_DIR" -name "aicrm_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
echo -e "${GREEN}✅ Backup script completed${NC}"