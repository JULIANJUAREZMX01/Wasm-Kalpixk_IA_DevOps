import os

import pytest


@pytest.fixture(autouse=True)
def set_env():
    os.environ["KALPIXK_API_KEY"] = "development_secret"
    os.environ["KALPIXK_ENV"] = "development"
