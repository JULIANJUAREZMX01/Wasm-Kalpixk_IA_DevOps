import os

import pytest

from python.db.database import init_db


@pytest.fixture(autouse=True)
def set_env():
    os.environ["KALPIXK_API_KEY"] = "development_secret"
    os.environ["KALPIXK_ENV"] = "development"
    os.environ["KALPIXK_DB_PATH"] = "./test_kalpixk_alerts.db"


@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    yield
    if os.path.exists("./test_kalpixk_alerts.db"):
        try:
            os.remove("./test_kalpixk_alerts.db")
        except PermissionError:
            pass
