import json
import os
from datetime import UTC, datetime

import aiosqlite
from loguru import logger

# Whitelist of allowed columns for the alerts table to prevent SQL Injection
ALLOWED_COLUMNS = {
    "ts", "ip", "anomaly_score", "event_type", "severity",
    "technique", "confidence", "features_json", "source"
}


def get_db_path():
    return os.getenv("KALPIXK_DB_PATH", "./kalpixk_alerts.db")

async def init_db():
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,           -- ISO8601 timestamp
              ip TEXT,
              anomaly_score REAL NOT NULL,
              event_type TEXT,
              severity TEXT,              -- LOW / HIGH / CRITICAL
              technique TEXT,
              confidence REAL,
              features_json TEXT,         -- JSON array of 32 floats (optional, for forensics)
              source TEXT DEFAULT 'agent' -- 'agent' or 'browser'
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
        await db.commit()

async def insert_alert(alert_dict):
    async with aiosqlite.connect(get_db_path()) as db:
        # Filter input against whitelist to prevent SQL Injection in column names
        filtered_data = {}
        for k, v in alert_dict.items():
            if k in ALLOWED_COLUMNS:
                filtered_data[k] = v
            else:
                logger.warning(f"Skipping invalid alert field: {k}")

        if not filtered_data and alert_dict:
            logger.error("Attempted to insert alert with only invalid fields")
            return

        # Convert features_json if it is a list
        features = filtered_data.get("features_json")
        if isinstance(features, list):
            filtered_data["features_json"] = json.dumps(features)

        # Ensure timestamp if not provided
        if "ts" not in filtered_data:
            filtered_data["ts"] = datetime.now(UTC).isoformat()

        columns = ", ".join(filtered_data.keys())
        placeholders = ", ".join([":" + k for k in filtered_data.keys()])
        query = f"INSERT INTO alerts ({columns}) VALUES ({placeholders})"

        await db.execute(query, filtered_data)
        await db.commit()

async def get_alerts(limit=100, severity_filter=None, since_ts=None):
    # Harden limit to prevent resource exhaustion or bypass via -1
    limit = max(1, min(500, int(limit)))
    db_path = get_db_path()
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []

    if severity_filter:
        query += " AND severity = ?"
        params.append(severity_filter)

    if since_ts:
        query += " AND ts >= ?"
        params.append(since_ts)

    query += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            alerts = []
            for row in rows:
                alert = dict(row)
                if alert.get("features_json"):
                    try:
                        alert["features_json"] = json.loads(alert["features_json"])
                    except Exception:
                        pass
                alerts.append(alert)

            # Get total count
            count_query = "SELECT COUNT(*) FROM alerts WHERE 1=1"
            count_params = []
            if severity_filter:
                count_query += " AND severity = ?"
                count_params.append(severity_filter)
            if since_ts:
                count_query += " AND ts >= ?"
                count_params.append(since_ts)

            async with db.execute(count_query, count_params) as count_cursor:
                total = (await count_cursor.fetchone())[0]

            return alerts, total


async def insert_alerts(alerts_list):
    if not alerts_list:
        return

    filtered_alerts = []
    for alert_dict in alerts_list:
        filtered_data = {}
        for k, v in alert_dict.items():
            if k in ALLOWED_COLUMNS:
                filtered_data[k] = v

        if not filtered_data:
            continue

        features = filtered_data.get("features_json")
        if isinstance(features, list):
            filtered_data["features_json"] = json.dumps(features)
        if "ts" not in filtered_data:
            filtered_data["ts"] = datetime.now(UTC).isoformat()

        filtered_alerts.append(filtered_data)

    if not filtered_alerts:
        return

    # Ensure all dicts have the same keys for executemany with named placeholders.
    # We use the union of all keys found in the filtered alerts.
    all_keys = set()
    for a in filtered_alerts:
        all_keys.update(a.keys())

    all_keys = sorted(list(all_keys)) # Deterministic order
    for a in filtered_alerts:
        for k in all_keys:
            if k not in a:
                a[k] = None

    db_path = get_db_path()
    async with aiosqlite.connect(db_path) as db:
        columns = ", ".join(all_keys)
        placeholders = ", ".join([":" + k for k in all_keys])
        query = f"INSERT INTO alerts ({columns}) VALUES ({placeholders})"

        await db.executemany(query, filtered_alerts)
        await db.commit()
