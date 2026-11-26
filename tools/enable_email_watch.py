import sqlite3

conn = sqlite3.connect(r'D:\projects\acesi\ace_memory.db')
conn.execute(
    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
    ('email_watch_enabled', '1'),
)
conn.commit()
print('email_watch_enabled =',
      conn.execute("SELECT value FROM config WHERE key = ?",
                   ('email_watch_enabled',)).fetchone()[0])
conn.close()
