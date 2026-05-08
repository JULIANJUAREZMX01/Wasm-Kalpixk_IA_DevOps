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
    # Mock close and accept as async
    async def mock_close(code=None): pass
    async def mock_accept(): pass

    ws.close = MagicMock(side_effect=mock_close)
    ws.accept = MagicMock(side_effect=mock_accept)

    print("Testing WebSocket in PRODUCTION without KALPIXK_API_KEY...")
    await ws_stream(ws, token=None)

    if ws.accept.called:
        print("VULNERABLE: WebSocket accepted connection in production without an API key configured!")
        sys.exit(1)

    if ws.close.called:
        code = ws.close.call_args[1].get('code')
        print(f"SAFE: WebSocket connection closed as expected with code {code}.")
    else:
        print("UNEXPECTED: WebSocket neither accepted nor closed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_auth_bypass())
