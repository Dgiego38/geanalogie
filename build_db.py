import sqlite3

conn = sqlite3.connect("genealogie.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS individuals (
    id TEXT PRIMARY KEY,
    firstname TEXT,
    lastname TEXT
)
""")

conn.commit()
conn.close()

print("Base créée")