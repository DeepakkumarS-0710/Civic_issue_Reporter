import sqlite3
import os

def init_db():
    os.makedirs("instance", exist_ok=True)
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Create reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            location TEXT NOT NULL,
            image_filename TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # Insert admin
    cursor.execute("INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)",
                   ('admin@gov', 'admin123', 'admin'))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
