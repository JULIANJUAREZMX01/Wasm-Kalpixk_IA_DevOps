import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Mock dependencies
sys.modules['msgpack'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['python.models.ensemble'] = MagicMock()
sys.modules['python.utils.device'] = MagicMock()
sys.modules['slowapi'] = MagicMock()
sys.modules['slowapi.util'] = MagicMock()
sys.modules['slowapi.errors'] = MagicMock()

# Set env to production but no key
os.environ["KALPIXK_ENV"] = "production"
if "KALPIXK_API_KEY" in os.environ:
    del os.environ["KALPIXK_API_KEY"]

from python.api.kalpixk_api import ws_stream

async def test_auth_bypass():
    ws = MagicMock()
    ws.close = MagicMock(side_effect=asyncio.Future)
    ws.close.return_value = None
    ws.accept = MagicMock(side_effect=asyncio.Future)
    ws.accept.return_value = None

    # Call ws_stream(ws, token=None)
    try:
        await ws_stream(ws, token=None)
    except Exception as e:
        print(f"Caught exception: {e}")

    # Check if ws.accept was called
    if ws.accept.called:
        print("VULNERABLE: WebSocket accepted without token in production!")
    else:
        print("SAFE: WebSocket not accepted.")

if __name__ == "__main__":
    asyncio.run(test_auth_bypass())
