"""
python/utils/wms_connector.py
──────────────────────────────
Manhattan WMS / IBM DB2 Connector — Kalpixk SIEM.

Streams audit logs from CEDIS Cancún (IBM DB2) and converts them
to Kalpixk's canonical log format for the WASM parser engine.

Modes:
  - "file"  : tail a DB2 audit log file (production)
  - "db2"   : live DRDA connection via ibm_db (requires driver)
  - "mock"  : synthetic realistic logs for dev/testing

SECURITY:
  Connection string is ALWAYS loaded from environment variable.
  Never hardcoded. See .env.example.

SAC CLI integration:
  sac nexus run etl --source=db2 --target=kalpixk --mode=delta
"""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Generator, Optional

logger = logging.getLogger("kalpixk.wms_connector")

# ── SAC-monitored tables (22 critical queries in the WMS) ────────────────────
SAC_TABLES = [
    "INVENTORY", "SHIPMENT", "ORDER_HEADER", "ORDER_DETAIL",
    "EMPLOYEE",  "WMS_USER", "VENDOR",       "BILLING",
    "CARTON",    "TASK_DETAIL", "PICK_DETAIL", "RECEIPT_DETAIL",
    "LOCATION",  "ITEM_MASTER", "WAVE",        "PUTAWAY_DIRECTIVE",
    "CONTAINER", "CARRIER",     "CLIENT",      "ZONE",
    "WORK_QUEUE", "LABOR_ACTIVITY",
]

AUTHIDS_NORMAL  = ["WMS_OPS", "WMS_APP", "CEDIS_ETL", "REPORT_USER", "MONITOR"]
AUTHIDS_SUSPECT = ["ROOT", "UNKNOWN", "TEST_USER", "BACKUP_OP"]
HOSTNAMES_CEDIS = ["cedis_427", "cedis_428", "cedis_mgt01", "appserver01", "cedis_backup"]


@dataclass
class WmsLogEntry:
    """Structured representation of a single DB2 audit log entry."""
    timestamp:    datetime
    authid:       str
    hostname:     str
    operation:    str          # EXECUTE, CONNECT, DISCONNECT, GRANT, REVOKE, etc.
    statement:    str
    return_code:  int          # SQLCODE: 0 = success, negative = error/denial
    rows_affected: int
    database:     str = "WMSDB"
    object_name:  Optional[str] = None   # Table or object involved

    def to_kalpixk_log(self) -> str:
        """
        Convert to the format expected by Db2AuditParser in kalpixk-core.
        Format matches parsers.rs::Db2AuditParser.
        """
        ts = self.timestamp.strftime("%Y-%m-%d-%H.%M.%S.%f")[:23]
        parts = [
            f"TIMESTAMP={ts}",
            f"AUTHID={self.authid}",
            f"HOSTNAME={self.hostname}",
            f"DATABASE={self.database}",
            f"OPERATION={self.operation}",
            f"SQLCODE={self.return_code}",
            f"ROWS={self.rows_affected}",
        ]
        # Truncate statement to avoid overwhelming the parser
        stmt = self.statement[:512].replace("\n", " ").strip()
        parts.append(f"SQL={stmt}")
        return " ".join(parts)

    @property
    def is_suspicious(self) -> bool:
        s = self.statement.upper()
        return any(kw in s for kw in ["DROP", "TRUNCATE", "GRANT", "REVOKE",
                                       "EXPORT", "LOAD", "IMPORT", "CREATE USER",
                                       "ALTER USER", "ALTER TABLE"])

    @property
    def severity_hint(self) -> float:
        """Local severity estimate before WASM parsing."""
        if self.return_code < 0:        return 0.3   # Denied/error
        if "DROP"      in self.statement.upper(): return 0.95
        if "EXPORT"    in self.statement.upper(): return 0.80
        if "GRANT"     in self.statement.upper(): return 0.75
        if "IMPORT"    in self.statement.upper(): return 0.70
        if self.authid in AUTHIDS_SUSPECT:        return 0.65
        if self.rows_affected > 100_000:          return 0.60
        return 0.15


# ── Connector ─────────────────────────────────────────────────────────────────

class WmsConnector:
    """
    Streams IBM DB2 audit logs and converts them to Kalpixk format.

    Quick start:
        connector = WmsConnector(mode="mock")
        for log_line in connector.stream():
            event = parse_log_line(log_line, "db2")   # WASM call
    """

    def __init__(
        self,
        mode: str = "mock",
        audit_log_path: str = "/var/log/db2/db2audit.log",
        batch_size: int = 100,
    ):
        assert mode in ("file", "db2", "mock"), f"Invalid mode: {mode}"
        self.mode           = mode
        self.audit_log_path = audit_log_path
        self.batch_size     = batch_size
        self._connection    = None

        if mode == "db2":
            self._connect_db2()

        logger.info(f"WmsConnector initialized: mode={mode}")

    # ── DB2 live connection ───────────────────────────────────────────────────

    def _connect_db2(self):
        """Connect to IBM DB2 via DRDA. Conn string from env."""
        conn_str = os.environ.get("KALPIXK_DB2_CONN")
        if not conn_str:
            logger.warning("KALPIXK_DB2_CONN not set — falling back to file mode")
            self.mode = "file"
            return
        try:
            import ibm_db  # type: ignore
            self._connection = ibm_db.connect(conn_str, "", "")
            logger.info("DB2 connection established")
        except Exception as e:
            logger.error(f"DB2 connection failed: {e} — falling back to file mode")
            self.mode = "file"

    # ── Streaming ────────────────────────────────────────────────────────────

    def stream(self) -> Generator[str, None, None]:
        """
        Yield log lines formatted for the Kalpixk WASM parser (db2 source).
        Runs indefinitely in file/mock modes.
        """
        dispatch = {
            "mock": self._stream_mock,
            "file": self._stream_file,
            "db2":  self._stream_db2_query,
        }
        yield from dispatch[self.mode]()

    def stream_batch(self, n: int = 100) -> list[str]:
        """Return a batch of N log lines (useful for REST API feeding)."""
        result = []
        for line in self.stream():
            result.append(line)
            if len(result) >= n:
                break
        return result

    # ── Mock stream (dev/testing) ─────────────────────────────────────────────

    def _stream_mock(self) -> Generator[str, None, None]:
        """
        Generates realistic mock DB2 logs with occasional anomalies.
        Suitable for local development and CI testing.
        """
        rng = random.Random(42)
        base_time = datetime.now(timezone.utc)
        idx = 0

        # Anomaly injection schedule (every ~50 events inject 1 anomaly)
        ANOMALY_RATE = 0.02

        while True:
            idx += 1
            now = base_time + timedelta(seconds=idx * 5)
            is_anomaly = rng.random() < ANOMALY_RATE

            entry = self._generate_mock_entry(rng, now, is_anomaly)
            yield entry.to_kalpixk_log()

            # Simulate real-time pace in streaming mode
            # (remove sleep for batch generation)
            # time.sleep(0.1)

    def _generate_mock_entry(
        self, rng: random.Random, ts: datetime, is_anomaly: bool
    ) -> WmsLogEntry:
        table = rng.choice(SAC_TABLES)

        if is_anomaly:
            # Inject anomalous patterns
            anomaly_type = rng.choice([
                "drop_table", "bulk_export", "privilege_grant",
                "off_hours_access", "unknown_user", "mass_select",
            ])

            if anomaly_type == "drop_table":
                return WmsLogEntry(
                    timestamp=ts, authid="ROOT",
                    hostname="10.0.3.99",
                    operation="EXECUTE",
                    statement=f"DROP TABLE {table}",
                    return_code=-551, rows_affected=0,
                )
            elif anomaly_type == "bulk_export":
                return WmsLogEntry(
                    timestamp=ts, authid=rng.choice(AUTHIDS_SUSPECT),
                    hostname="cedis_backup",
                    operation="EXPORT",
                    statement=f"EXPORT TO /tmp/dump_{ts.strftime('%H%M')}.csv OF DEL "
                              f"SELECT * FROM {table}",
                    return_code=0, rows_affected=rng.randint(10_000, 500_000),
                )
            elif anomaly_type == "privilege_grant":
                return WmsLogEntry(
                    timestamp=ts, authid="WMS_OPS",
                    hostname=rng.choice(HOSTNAMES_CEDIS),
                    operation="GRANT",
                    statement=f"GRANT SELECT, INSERT, UPDATE ON {table} TO PUBLIC",
                    return_code=0, rows_affected=0,
                )
            elif anomaly_type == "off_hours_access":
                off_ts = ts.replace(hour=rng.randint(1, 5))
                return WmsLogEntry(
                    timestamp=off_ts, authid=rng.choice(AUTHIDS_SUSPECT),
                    hostname="10.0.99.44",
                    operation="EXECUTE",
                    statement=f"SELECT * FROM {table} FETCH FIRST 1000000 ROWS ONLY",
                    return_code=0, rows_affected=rng.randint(50_000, 200_000),
                )
            elif anomaly_type == "unknown_user":
                return WmsLogEntry(
                    timestamp=ts, authid="UNKNOWN_USER",
                    hostname="external_host",
                    operation="CONNECT",
                    statement="CONNECT TO WMSDB",
                    return_code=-1060, rows_affected=0,
                )
            else:  # mass_select
                return WmsLogEntry(
                    timestamp=ts, authid=rng.choice(AUTHIDS_NORMAL),
                    hostname=rng.choice(HOSTNAMES_CEDIS),
                    operation="EXECUTE",
                    statement=f"SELECT * FROM {table}",
                    return_code=0, rows_affected=rng.randint(500_000, 2_000_000),
                )

        # Normal operation
        loc_id = f"A-{rng.randint(1, 99):02d}"
        op_type = rng.choices(
            ["SELECT", "UPDATE", "INSERT", "DELETE"],
            weights=[0.70, 0.15, 0.10, 0.05]
        )[0]

        stmt_map = {
            "SELECT": f"SELECT LOC_ID, QTY, ITEM_ID FROM {table} WHERE LOC_ID='{loc_id}'",
            "UPDATE": f"UPDATE {table} SET QTY=QTY-1 WHERE LOC_ID='{loc_id}' AND ITEM_ID='{rng.randint(100,999):03d}'",
            "INSERT": f"INSERT INTO {table} (LOC_ID, QTY, ITEM_ID, TS) VALUES ('{loc_id}', 1, '{rng.randint(100,999):03d}', CURRENT TIMESTAMP)",
            "DELETE": f"DELETE FROM {table} WHERE SHIP_ID='{rng.randint(10000, 99999)}'",
        }

        return WmsLogEntry(
            timestamp=ts,
            authid=rng.choice(AUTHIDS_NORMAL),
            hostname=rng.choice(HOSTNAMES_CEDIS),
            operation="EXECUTE",
            statement=stmt_map[op_type],
            return_code=0,
            rows_affected=rng.randint(1, 100),
            object_name=table,
        )

    # ── File tail stream ──────────────────────────────────────────────────────

    def _stream_file(self) -> Generator[str, None, None]:
        """Tail the DB2 audit log file in real-time."""
        import subprocess
        try:
            proc = subprocess.Popen(
                ["tail", "-F", self.audit_log_path],
                stdout=subprocess.PIPE, text=True, bufsize=1,
            )
            logger.info(f"Tailing {self.audit_log_path}")
            for line in proc.stdout:
                if line.strip():
                    yield line.strip()
        except FileNotFoundError:
            logger.warning(f"Audit log not found: {self.audit_log_path} — switching to mock")
            self.mode = "mock"
            yield from self._stream_mock()

    # ── DB2 query stream ──────────────────────────────────────────────────────

    def _stream_db2_query(self) -> Generator[str, None, None]:
        """Stream recent audit records via direct DB2 query (delta mode)."""
        if not self._connection:
            logger.warning("No DB2 connection — switching to file mode")
            self.mode = "file"
            yield from self._stream_file()
            return

        try:
            import ibm_db  # type: ignore
            last_ts = datetime.now(timezone.utc) - timedelta(minutes=5)

            while True:
                sql = f"""
                    SELECT TIMESTAMP, AUTHID, APPID, OBJNAME, STMTTEXT, SQLCODE
                    FROM SYSIBM.SYSAUDIT
                    WHERE TIMESTAMP > '{last_ts.strftime("%Y-%m-%d %H:%M:%S")}'
                    ORDER BY TIMESTAMP ASC
                    FETCH FIRST {self.batch_size} ROWS ONLY
                """
                stmt = ibm_db.exec_immediate(self._connection, sql)
                row = ibm_db.fetch_assoc(stmt)
                while row:
                    entry = WmsLogEntry(
                        timestamp=row.get("TIMESTAMP", datetime.now(timezone.utc)),
                        authid=row.get("AUTHID", "UNKNOWN"),
                        hostname=row.get("APPID", "unknown"),
                        operation="EXECUTE",
                        statement=row.get("STMTTEXT", "")[:512],
                        return_code=int(row.get("SQLCODE", 0) or 0),
                        rows_affected=0,
                    )
                    last_ts = entry.timestamp
                    yield entry.to_kalpixk_log()
                    row = ibm_db.fetch_assoc(stmt)

                time.sleep(5)  # Poll interval

        except Exception as e:
            logger.error(f"DB2 stream error: {e}")

    # ── Stats ────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "mode": self.mode,
            "audit_log_path": self.audit_log_path,
            "connected": self._connection is not None,
            "monitored_tables": len(SAC_TABLES),
        }
