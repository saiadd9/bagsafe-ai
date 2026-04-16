from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=MEMORY")
        connection.execute("PRAGMA temp_store=MEMORY")
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS baggage_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    passenger_name TEXT NOT NULL,
                    booking_reference TEXT NOT NULL,
                    tag_number TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    layover_minutes INTEGER NOT NULL,
                    transfer_points INTEGER NOT NULL,
                    terminal_distance_meters INTEGER NOT NULL,
                    incoming_delay_minutes INTEGER NOT NULL,
                    international_transfer INTEGER NOT NULL,
                    checked_bags INTEGER NOT NULL,
                    priority_status INTEGER NOT NULL,
                    baggage_type TEXT NOT NULL,
                    risk_category TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_record(self, record: dict[str, object]) -> None:
        fields = ", ".join(record.keys())
        placeholders = ", ".join(f":{key}" for key in record)
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO baggage_records ({fields}) VALUES ({placeholders})",
                record,
            )

    def fetch_records(self, search_term: str = "") -> list[sqlite3.Row]:
        query = """
            SELECT *
            FROM baggage_records
            WHERE (
                :search = ''
                OR passenger_name LIKE :pattern
                OR booking_reference LIKE :pattern
                OR tag_number LIKE :pattern
                OR flight_number LIKE :pattern
                OR risk_category LIKE :pattern
            )
            ORDER BY id DESC
        """
        pattern = f"%{search_term.strip()}%"
        with self._connect() as connection:
            return connection.execute(query, {"search": search_term.strip(), "pattern": pattern}).fetchall()

    def delete_record(self, record_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM baggage_records WHERE id = ?", (record_id,))
