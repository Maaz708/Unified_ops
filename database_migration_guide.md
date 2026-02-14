# Database Migration Guide

## Option 1: Render Database + Migration (Recommended)

### Step 1: Create Production Database on Render
1. In Render dashboard, click "New" → "PostgreSQL"
2. Name: `hackathon-db`
3. Plan: Free (or paid for production)
4. Wait for database to be ready

### Step 2: Get Production Database URL
1. Go to your database service in Render
2. Copy the "Connection" URL (internal)
3. It looks like: `postgresql://user:pass@host:port/dbname`

### Step 3: Run Migration Script
```bash
# Install required packages
pip install sqlalchemy psycopg2-binary

# Run migration
python migrate_database.py "postgresql://user:pass@host:port/dbname"
```

## Option 2: Manual SQL Export/Import

### From Local to Production:

1. **Export Local Data:**
```bash
# If using SQLite (local)
sqlite3 app.db .dump > local_data.sql

# If using PostgreSQL (local)
pg_dump local_db > local_data.sql
```

2. **Import to Production:**
```bash
# Connect to Render database
psql "postgresql://user:pass@host:port/dbname" < local_data.sql
```

## Option 3: Use Render's Web Interface

1. **Access pgAdmin:**
   - Go to your database in Render
   - Click "Connect" → "External Connection"
   - Use pgAdmin or similar tool

2. **Manual Copy:**
   - Connect to both databases
   - Copy table by table
   - Preserve relationships

## Important Notes:

### ID Conflicts
- Production database will generate new IDs
- Foreign key relationships will be preserved
- Workspace UUIDs will remain the same

### Sensitive Data
- Check for any test data you don't want in production
- Update email addresses if needed
- Verify API keys and secrets

### Data Types
- SQLite to PostgreSQL conversion may need type adjustments
- Dates and timestamps usually convert fine
- JSON fields work in both

## Post-Migration Checklist:

1. **Verify Data Count:**
```sql
-- Check record counts
SELECT COUNT(*) FROM workspaces;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM booking_types;
```

2. **Test Key Functionality:**
   - Login with existing users
   - Check workspace data
   - Verify booking types
   - Test availability slots

3. **Update Environment Variables:**
   - Set new DATABASE_URL in production
   - Test API health endpoint

## Troubleshooting:

### Common Issues:
1. **Foreign Key Constraints:** Import in correct order
2. **Data Type Mismatches:** Adjust column types
3. **Large Datasets:** Import in batches

### Recovery:
- Keep local database backup
- Test migration on staging first
- Document the process

## Automation:

For future deployments, consider:
1. **Alembic migrations** for schema changes
2. **CI/CD pipeline** for automated migrations
3. **Backup strategy** for production data
