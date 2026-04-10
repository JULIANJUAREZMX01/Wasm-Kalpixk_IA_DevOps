"""
Manhattan WMS / IBM DB2 Connector — Kalpixk SIEM
Adapts the 22 SAC queries from CEDIS Cancún to Kalpixk log format.
SECURITY: Connection string loaded from env — never hardcoded.
"""
import logging
import os
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger("kalpixk.wms")

@dataclass
class WmsLogEntry:
    timestamp: datetime
    authid: str
    hostname: str
    sql: str
    return_code: int
    rows_affected: int
    raw: str

    def to_kalpixk_log(self) -> str:
        """Convert to format expected by Db2AuditParser."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (f"TIMESTAMP={ts} AUTHID={self.authid} "
                f"HOSTNAME={self.hostname} SQL={self.sql} "
                f"SQLCODE={self.return_code} ROWS={self.rows_affected}")


class WmsConnector:
    """
    Reads IBM DB2 audit logs from Manhattan WMS.
    Supports: file-based audit logs, live DRDA connection, mock mode.
    """

    SAC_MONITORED_TABLES = [
        "INVENTORY", "SHIPMENT", "ORDER_HEADER", "ORDER_DETAIL",
        "EMPLOYEE", "WMS_USER", "VENDOR", "BILLING", "CARTON",
        "TASK_DETAIL", "PICK_DETAIL", "RECEIPT_DETAIL",
    ]

    def __init__(self, mode: str = "file"):
        self.mode = mode  # "file" | "db2" | "mock"
        self._connection = None
        if mode == "db2":
            self._init_db2()
        logger.info(f"WmsConnector initialized in mode={mode}")

    def _init_db2(self):
        try:
            import ibm_db
            conn_str = os.environ.get("KALPIXK_DB2_CONN")
            if not conn_str:
                raise ValueError("KALPIXK_DB2_CONN env var missing")
            self._connection = ibm_db.connect(conn_str, "", "")
            logger.info("DB2 connection established")
        except Exception as e:
            logger.warning(f"DB2 connection failed, falling back to file mode: {e}")
            self.mode = "file"

    def stream_audit_logs(
        self,
        audit_log_path: str = "/var/log/db2/db2audit.log",
        tail: bool = True,
    ) -> Generator[str, None, None]:
        """Stream DB2 audit log entries as Kalpixk-formatted log strings."""
        if self.mode == "mock":
            yield from self._mock_logs()
            return

        import subprocess
        cmd = ["tail", "-f", audit_log_path] if tail else ["cat", audit_log_path]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
            for line in proc.stdout:
                if line.strip():
                    yield line.strip()
        except FileNotFoundError:
            logger.warning(f"Audit log not found: {audit_log_path}. Using mock.")
            yield from self._mock_logs()

    def _mock_logs(self) -> Generator[str, None, None]:
        """Generate realistic mock logs for development/testing."""
        import random
        from datetime import timedelta

        templates = [
            "TIMESTAMP={ts} AUTHID=WMS_OPS HOSTNAME=cedis_427 SQL=SELECT * FROM INVENTORY WHERE LOC_ID='{loc}' SQLCODE=0 ROWS={n}",
            "TIMESTAMP={ts} AUTHID=WMS_OPS HOSTNAME=cedis_427 SQL=UPDATE SHIPMENT SET STATUS='SHIPPED' WHERE SHIP_ID='{sid}' SQLCODE=0 ROWS=1",
            "TIMESTAMP={ts} AUTHID=ROOT HOSTNAME=cedis_427 SQL=EXPORT TO /tmp/data.csv OF DEL SELECT * FROM ORDER_HEADER SQLCODE=0 ROWS={n}",
            "TIMESTAMP={ts} AUTHID=UNKNOWN HOSTNAME=10.0.3.99 SQL=DROP TABLE WMS_USER SQLCODE=-551 ROWS=0",
            "TIMESTAMP={ts} AUTHID=WMS_OPS HOSTNAME=cedis_427 SQL=GRANT SELECT ON INVENTORY TO PUBLIC SQLCODE=0 ROWS=0",
        ]
        base_time = datetime.now(UTC)
        for i in range(100): # Limited to 100 for shorter runs
            ts = (base_time - timedelta(seconds=i * 30)).strftime("%Y-%m-%d %H:%M:%S")
            tpl = random.choice(templates)
            yield tpl.format(
                ts=ts, loc=f"A-{random.randint(1,99):02d}", n=random.randint(1, 5000),
                sid=f"SHP{random.randint(10000, 99999)}"
            )
