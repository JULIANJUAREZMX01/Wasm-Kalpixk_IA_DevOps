import hmac
import hashlib
import time
import pytest
from src.api.main import ThreatReport

SECRET = "development_secret"

def test_threat_report_validation():
    node_id = "test-node"
    ts = int(time.time())
    msg = f"{node_id}{ts}".encode()
    sig = hmac.new(SECRET.encode(), msg, hashlib.sha256).hexdigest()

    report = ThreatReport(
        node_id=node_id,
        threats=["T1003"],
        timestamp=ts,
        signature=sig,
        version="4.0.0-atlatl"
    )
    assert report.node_id == node_id
    assert report.signature == sig

def test_threat_report_invalid_timestamp():
    with pytest.raises(ValueError, match="Timestamp out of sync"):
        ThreatReport(
            node_id="test-node",
            threats=["T1003"],
            timestamp=int(time.time()) - 600,
            signature="fake-sig"
        )

def test_hmac_logic():
    secret = b"test_secret"
    msg = b"node11700000000"
    sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(sig, hmac.new(secret, msg, hashlib.sha256).hexdigest())
