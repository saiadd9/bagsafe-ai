import sqlite3
from pathlib import Path

db_path = Path("artifacts") / "bagsafe_shared.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=MEMORY")

cursor.execute("DROP TABLE IF EXISTS records")
cursor.execute("""
CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    passengerName TEXT NOT NULL,
    bookingReference TEXT NOT NULL,
    bagTag TEXT NOT NULL,
    flightNumber TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    layoverMinutes INTEGER NOT NULL,
    transferPoints INTEGER NOT NULL,
    terminalDistance INTEGER NOT NULL,
    incomingDelay INTEGER NOT NULL,
    checkedBags INTEGER NOT NULL,
    baggageType TEXT NOT NULL,
    priorityStatus INTEGER NOT NULL DEFAULT 0,
    internationalTransfer INTEGER NOT NULL DEFAULT 0,
    route TEXT NOT NULL,
    risk TEXT NOT NULL,
    score INTEGER NOT NULL,
    savedAt TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Database created!")
