#!/usr/bin/env python3
"""
Simple PostgreSQL Migration using pg_dump
"""

import subprocess
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python simple_migration.py <production_database_url>")
        sys.exit(1)
    
    prod_db_url = sys.argv[1]
    
    print("📤 Exporting local PostgreSQL data...")
    
    # Export from local PostgreSQL
    export_cmd = [
        "pg_dump",
        "-h", "localhost",
        "-U", "postgres",
        "-d", "hac_db",
        "--no-owner",
        "--no-privileges",
        "--clean",
        "--if-exists",
        "-f", "local_data.sql"
    ]
    
    try:
        subprocess.run(export_cmd, check=True)
        print("✅ Local data exported to local_data.sql")
    except subprocess.CalledProcessError as e:
        print(f"❌ Export failed: {e}")
        print("Make sure PostgreSQL is running and accessible")
        return
    
    print("📥 Importing to production database...")
    
    # Import to production PostgreSQL
    import_cmd = [
        "psql",
        prod_db_url,
        "-f", "local_data.sql"
    ]
    
    try:
        subprocess.run(import_cmd, check=True)
        print("✅ Data imported to production database!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Clean up
    import os
    try:
        os.remove("local_data.sql")
        print("🧹 Cleaned up temporary files")
    except:
        pass

if __name__ == "__main__":
    main()
