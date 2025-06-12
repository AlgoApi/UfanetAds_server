import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
from os import getenv
load_dotenv()

DATABASE_URL = getenv("DATABASE_URL")

# Создаём асинхронный движок (echo=True только для отладки)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Зависимость FastAPI: получение сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
