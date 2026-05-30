import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

db_path = Path(os.environ.get("PYTEST_TMPDIR", tempfile.gettempdir())) / f"wakatoken-test-{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{db_path.resolve().as_posix()}"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
