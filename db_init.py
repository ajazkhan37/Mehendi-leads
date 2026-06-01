import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'leads.db')


LEAD_COLUMNS = {
    # new fields
    "pincode": "TEXT",
    "whatsapp_number": "TEXT",
    "full_address": "TEXT",
    "event_type": "TEXT",
    "lead_status": "TEXT",
    "maps_link": "TEXT",

    # existing fields (keep for CREATE TABLE default)
    "name": "TEXT NOT NULL",
    "phone": "TEXT NOT NULL",
    "email": "TEXT",
    "event_date": "DATE",
    "location": "TEXT",
    "budget": "TEXT",
    "additional_notes": "TEXT",
}


def column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [row[1] for row in cursor.fetchall()]
    return column_name in cols


def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            event_date DATE,
            location TEXT,
            budget TEXT,
            additional_notes TEXT,
            pincode TEXT,
            whatsapp_number TEXT,
            full_address TEXT,
            event_type TEXT,
            lead_status TEXT DEFAULT 'New',
            maps_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    # Gallery table (for homepage portfolio)
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS gallery_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    # Hero Images table (single active hero banner)
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS hero_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    # Migration for existing databases: add missing columns

    for col, col_type in LEAD_COLUMNS.items():
        if col in {"name", "phone"}:
            continue
        if not column_exists(cursor, "leads", col):
            default = ""
            if col == "lead_status":
                default = " DEFAULT 'New'"
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}{default}")

    # Ensure lead_status isn't NULL for older rows
    cursor.execute("UPDATE leads SET lead_status = 'New' WHERE lead_status IS NULL")

    conn.commit()
    conn.close()
    print(f"Database initialized/migrated at {db_path}")


if __name__ == "__main__":
    init_db()
