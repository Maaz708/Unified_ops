"""
One-off migration: add booking_type_id to form_templates.
Run from project root: python -m app.migrations.add_form_templates_booking_type_id
"""
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    from app.core.config import settings
    import psycopg2

    url = str(settings.database_url).replace("+psycopg2", "")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE form_templates
                ADD COLUMN IF NOT EXISTS booking_type_id UUID NULL
                REFERENCES booking_types(id) ON DELETE SET NULL;
            """)
        print("Added form_templates.booking_type_id (or column already existed).")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
