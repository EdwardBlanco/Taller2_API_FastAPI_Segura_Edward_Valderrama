from collections.abc import Generator

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.limiter import limiter
from app.main import app

settings = get_settings()
test_db_url = settings.test_database_url or "postgresql+psycopg://postgres:1234@localhost:5432/biblioteca_test"

test_engine = create_engine(test_db_url, echo=False)
TestingSessionLocal = sessionmaker(
    autoflush=False,
    expire_on_commit=False,
    bind=test_engine,
)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    limiter.reset()
    with TestingSessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE TABLE refresh_tokens, prestamos, libro_categoria, libros, categorias, autores, usuarios, socios RESTART IDENTITY CASCADE;"
            )
        )
        session.commit()
    yield
    limiter.reset()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session

