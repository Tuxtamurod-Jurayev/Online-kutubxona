from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import config

# Async Engine yaratish
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    future=True
)

# Async Session Factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Barcha jadvallarni ma'lumotlar bazasida yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
