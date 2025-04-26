from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings
from app.db.base_class import Base

from typing import AsyncGenerator



engine = create_async_engine(settings.get_url())

async_session = sessionmaker(
    engine, autocommit=False, autoflush=False, class_=AsyncSession
)

async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)