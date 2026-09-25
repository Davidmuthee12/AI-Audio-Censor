from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import db_settings

engine = create_async_engine(
    db_settings.DB_URL,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with async_session() as session:
        yield session
