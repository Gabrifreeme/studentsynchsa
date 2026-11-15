import sqlite3
c = sqlite3.connect(r"C:\Users\chris\LipSyncStudent\ace_memory.db")
n = c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
c.execute("DELETE FROM conversations")
c.commit()
n2 = c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
c.close()
print(f"deleted {n} rows, {n2} remain")
