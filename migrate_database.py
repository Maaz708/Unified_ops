#!/usr/bin/env python3
"""
Database Migration Script
Exports local database and imports to production database
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.core.database import Base
from app.models import *

def export_local_data():
    """Export data from local database"""
    # Use your actual local PostgreSQL database
    local_engine = create_engine("postgresql+psycopg2://postgres:blogroot@localhost:5432/hac_db")
    
    # Get all table data
    data = {}
    with local_engine.connect() as conn:
        for table_name in Base.metadata.tables.keys():
            try:
                result = conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = [dict(row._mapping) for row in result]
                if rows:  # Only add if there's data
                    data[table_name] = rows
                    print(f"  - {table_name}: {len(rows)} records")
                else:
                    print(f"  - {table_name}: 0 records")
            except Exception as e:
                print(f"  - {table_name}: Table not found or error ({e})")
                continue
    
    return data

def import_to_production(prod_db_url, data):
    """Import data to production database"""
    prod_engine = create_engine(prod_db_url)
    
    with prod_engine.connect() as conn:
        # Begin transaction
        trans = conn.begin()
        try:
            for table_name, rows in data.items():
                if rows:  # Only import if there's data
                    # Get table model
                    table = Base.metadata.tables[table_name]
                    
                    # Clear existing data (optional - remove if you want to keep existing)
                    conn.execute(text(f"DELETE FROM {table_name}"))
                    
                    # Insert new data
                    for row in rows:
                        # Remove auto-generated fields that might conflict
                        if 'id' in row and table_name not in ['workspaces', 'users', 'booking_types']:
                            # Keep IDs for reference tables, but let DB generate for main entities
                            pass
                        
                        # Build insert statement
                        columns = list(row.keys())
                        values = list(row.values())
                        placeholders = [f":{col}" for col in columns]
                        
                        insert_sql = f"""
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        """
                        
                        conn.execute(text(insert_sql), row)
            
            trans.commit()
            print("✅ Data imported successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Import failed: {e}")
            raise

def main():
    if len(sys.argv) != 2:
        print("Usage: python migrate_database.py <production_database_url>")
        sys.exit(1)
    
    prod_db_url = sys.argv[1]
    
    print("📤 Exporting local data...")
    data = export_local_data()
    
    print(f"📊 Found data for {len(data)} tables:")
    for table, rows in data.items():
        print(f"  - {table}: {len(rows)} records")
    
    print("📥 Importing to production...")
    import_to_production(prod_db_url, data)

if __name__ == "__main__":
    main()
