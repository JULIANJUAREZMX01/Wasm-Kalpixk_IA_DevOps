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

import numpy as np
import torch

from python.api.kalpixk_api import app, LogRequest

async def test_endpoints():
    print("Testing Pydantic models...")
    req = LogRequest(features=[0.0]*32)
    print("LogRequest created successfully.")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
