
import os
import secrets
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi import status as fastapi_status

# Mocking what's in python/api/kalpixk_api.py
API_KEY_NAME = "X-Kalpixk-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))
    expected_key = os.getenv("KALPIXK_API_KEY")

    if env == "production":
        if not expected_key:
            # from loguru import logger
            # logger.error("KALPIXK_API_KEY not set in production!")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
        if not api_key or not secrets.compare_digest(api_key, expected_key):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    else:
        if expected_key and (not api_key or not secrets.compare_digest(api_key, expected_key)):
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    return api_key

import asyncio

async def test():
    os.environ["KALPIXK_ENV"] = "production"
    os.environ["KALPIXK_API_KEY"] = "" # Empty to trigger the first error
    try:
        await verify_api_key(None)
    except NameError as e:
        print(f"Caught expected NameError: {e}")
    except Exception as e:
        print(f"Caught other exception: {type(e)} {e}")

if __name__ == "__main__":
    asyncio.run(test())
