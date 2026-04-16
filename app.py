import os
import sqlite3
import uuid
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join("artifacts", "bagsafe_shared.db"))
RECORD_COLUMNS = {
    "id": "TEXT PRIMARY KEY",
    "passengerName": "TEXT NOT NULL",
    "bookingReference": "TEXT NOT NULL",
    "bagTag": "TEXT NOT NULL",
    "flightNumber": "TEXT NOT NULL",
    "origin": "TEXT NOT NULL",
    "destination": "TEXT NOT NULL",
    "layoverMinutes": "INTEGER NOT NULL",
    "transferPoints": "INTEGER NOT NULL",
    "terminalDistance": "INTEGER NOT NULL",
    "incomingDelay": "INTEGER NOT NULL",
    "checkedBags": "INTEGER NOT NULL",
    "baggageType": "TEXT NOT NULL",
    "priorityStatus": "INTEGER NOT NULL DEFAULT 0",
    "internationalTransfer": "INTEGER NOT NULL DEFAULT 0",
    "route": "TEXT NOT NULL",
    "risk": "TEXT NOT NULL",
    "score": "INTEGER NOT NULL",
    "savedAt": "TEXT NOT NULL",
}


def get_db():
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=MEMORY")
    return conn


def ensure_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS records (
            {", ".join(f"{name} {definition}" for name, definition in RECORD_COLUMNS.items())}
        )
        """
    )

    existing_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(records)").fetchall()
    }
    missing_columns = [
        column for column in RECORD_COLUMNS if column not in existing_columns
    ]

    if missing_columns:
        cursor.execute("DROP TABLE IF EXISTS records")
        cursor.execute(
            f"""
            CREATE TABLE records (
                {", ".join(f"{name} {definition}" for name, definition in RECORD_COLUMNS.items())}
            )
            """
        )

    conn.commit()
    conn.close()


def normalize_record(data, record_id=None):
    return {
        "id": record_id or data.get("id") or str(uuid.uuid4()),
        "passengerName": str(data["passengerName"]).strip(),
        "bookingReference": str(data["bookingReference"]).strip().upper(),
        "bagTag": str(data["bagTag"]).strip().upper(),
        "flightNumber": str(data["flightNumber"]).strip().upper(),
        "origin": str(data["origin"]).strip().upper(),
        "destination": str(data["destination"]).strip().upper(),
        "layoverMinutes": int(data["layoverMinutes"]),
        "transferPoints": int(data["transferPoints"]),
        "terminalDistance": int(data["terminalDistance"]),
        "incomingDelay": int(data["incomingDelay"]),
        "checkedBags": int(data["checkedBags"]),
        "baggageType": str(data["baggageType"]).strip(),
        "priorityStatus": int(bool(data["priorityStatus"])),
        "internationalTransfer": int(bool(data["internationalTransfer"])),
        "route": str(data["route"]).strip(),
        "risk": str(data["risk"]).strip(),
        "score": int(data["score"]),
        "savedAt": str(data["savedAt"]).strip(),
    }


@app.route("/")
def home():
    ensure_db()
    return render_template("index.html")


@app.route("/records", methods=["GET"])
def records():
    ensure_db()
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM records ORDER BY savedAt DESC, rowid DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/records", methods=["POST"])
def create_record():
    ensure_db()
    payload = normalize_record(request.get_json(force=True))
    conn = get_db()
    conn.execute(
        """
        INSERT INTO records (
            id, passengerName, bookingReference, bagTag, flightNumber, origin,
            destination, layoverMinutes, transferPoints, terminalDistance,
            incomingDelay, checkedBags, baggageType, priorityStatus,
            internationalTransfer, route, risk, score, savedAt
        )
        VALUES (
            :id, :passengerName, :bookingReference, :bagTag, :flightNumber, :origin,
            :destination, :layoverMinutes, :transferPoints, :terminalDistance,
            :incomingDelay, :checkedBags, :baggageType, :priorityStatus,
            :internationalTransfer, :route, :risk, :score, :savedAt
        )
        """,
        payload,
    )
    conn.commit()
    conn.close()
    return jsonify(payload), 201


@app.route("/records/<record_id>", methods=["PUT"])
def update_record(record_id):
    ensure_db()
    payload = normalize_record(request.get_json(force=True), record_id=record_id)
    conn = get_db()
    cursor = conn.execute(
        """
        UPDATE records
        SET passengerName = :passengerName,
            bookingReference = :bookingReference,
            bagTag = :bagTag,
            flightNumber = :flightNumber,
            origin = :origin,
            destination = :destination,
            layoverMinutes = :layoverMinutes,
            transferPoints = :transferPoints,
            terminalDistance = :terminalDistance,
            incomingDelay = :incomingDelay,
            checkedBags = :checkedBags,
            baggageType = :baggageType,
            priorityStatus = :priorityStatus,
            internationalTransfer = :internationalTransfer,
            route = :route,
            risk = :risk,
            score = :score,
            savedAt = :savedAt
        WHERE id = :id
        """,
        payload,
    )
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"message": "Record not found"}), 404

    return jsonify(payload)


@app.route("/records/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    ensure_db()
    conn = get_db()
    cursor = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"message": "Record not found"}), 404

    return jsonify({"message": "Deleted"})


@app.route("/records", methods=["DELETE"])
def clear_records():
    ensure_db()
    conn = get_db()
    conn.execute("DELETE FROM records")
    conn.commit()
    conn.close()
    return jsonify({"message": "Cleared"})


if __name__ == "__main__":
    ensure_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
