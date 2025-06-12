# tests/conftest.py

from dotenv import load_dotenv
from os import getenv
load_dotenv()
import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx import ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app as fastapi_app
from db.dependencies import get_db
from db.base import Base


# Тестовая БД, не меняем URL
TEST_DATABASE_URL = getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://main:1232@178.12355:5232/u2ne23db"
)


@pytest.fixture(autouse=True)
def reset_schema_per_test():
    """
    Синхронно перед каждым тестом дропаем (если есть) и создаём схему.
    Т.к. это sync, проблем с loop-ами нет.
    """
    # строим sync-движок из того же URL, убирая +asyncpg
    sync_url = TEST_DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_url, echo=False, future=True)

    # drop_all без проверки (checkfirst=False) и заново create_all
    Base.metadata.drop_all(bind=sync_engine, checkfirst=True)
    Base.metadata.create_all(bind=sync_engine)

    yield  # <<< тест выполняется здесь

    # после теста снова чистим
    Base.metadata.drop_all(bind=sync_engine, checkfirst=False)
    sync_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """
    Асинхронная сессия к тестовой БД (единой на тест)
    """
    async_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await async_engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """
    HTTP-клиент, который во время теста будет отдавать в FastAPI наш test-session
    """
    # override get_db
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db  # type: ignore[attr-defined]

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()  # type: ignore[attr-defined]
