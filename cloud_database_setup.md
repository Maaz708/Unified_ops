# Cloud Database Setup Options

## Option 1: Railway (Easiest)
1. Create Railway account
2. Click "New Project" → "Add PostgreSQL"
3. Get connection string
4. Update DATABASE_URL in production

## Option 2: PlanetScale (MySQL-compatible)
1. Create PlanetScale account
2. Create new database
3. Get connection string
4. Update DATABASE_URL in production

## Option 3: Supabase (PostgreSQL + Features)
1. Create Supabase account
2. Create new project
3. Get connection string from Settings > Database
4. Update DATABASE_URL in production

## Option 4: AWS RDS (Most Control)
1. Create AWS account
2. Go to RDS dashboard
3. Create PostgreSQL instance
4. Configure security groups
5. Get connection string

## Option 5: Google Cloud SQL
1. Create Google Cloud account
2. Go to Cloud SQL
3. Create PostgreSQL instance
4. Get connection string

## Quick Setup with Railway:

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Create database
railway add postgresql

# 4. Get connection URL
railway variables get DATABASE_URL

# 5. Use this URL in your Render deployment
```

## Environment Variable Format:
```
postgresql://username:password@host:port/database_name
```

## Migration to Cloud Database:

### Step 1: Export Current Data
```bash
# If using SQLite locally
python export_from_sqlite.py

# If using PostgreSQL locally
pg_dump local_db > backup.sql
```

### Step 2: Import to Cloud
```bash
# Import to cloud database
psql "postgresql://user:pass@host:port/db" < backup.sql
```

### Step 3: Update Render Configuration
In your Render service settings:
- Set DATABASE_URL to your cloud database URL
- Remove the Render PostgreSQL service
- Keep your backend service pointing to cloud DB

## Benefits of Cloud Database:
- ✅ Persistent data across deployments
- ✅ Better performance
- ✅ Backup and restore
- ✅ Scalability
- ✅ Can use with any hosting provider

## Recommendation:
For your use case, **Railway** is the easiest option:
- Free tier available
- Simple setup
- Good performance
- Works well with Render
