import sqlite3

# Connect to SQLite database (or create it)
conn = sqlite3.connect('chat.db')
cursor = conn.cursor()

# Create table for chatbot intents
cursor.execute('''
    CREATE TABLE IF NOT EXISTS intents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT NOT NULL,
        pattern TEXT NOT NULL,
        response TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print("✅ Database and table created successfully.")
