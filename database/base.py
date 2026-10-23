from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from config import config

# Dvigatel sozlamalari (PostgreSQL va SQLite uchun optimallashgan)
is_sqlite = "sqlite" in config.DATABASE_URL.lower()

engine_kwargs = {
    "echo": False,
    "future": True,
}

if not is_sqlite:
    # PostgreSQL / Supabase uchun connection pool sozlamalari
    engine_kwargs.update({
        "pool_pre_ping": True,     # Uzilib qolgan sessiyalarni avtomatik tiklash
        "pool_recycle": 1800,      # Ulanishlarni har 30 daqiqada yangilash
        "pool_size": 10,           # Asosiy ulanishlar soni
        "max_overflow": 20         # Favqulodda qo'shimcha ulanishlar soni
    })

engine = create_async_engine(config.DATABASE_URL, **engine_kwargs)

# Agar SQLite ishlatilsa - Write-Ahead Logging (WAL) va tezlik pragma'larini yoqamiz
if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

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
    """Barcha jadvallarni ma'lumotlar bazasida xavfsiz yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Bot to'xtatilganda ma'lumotlar bazasi ulanishlarini toza yopish"""
    await engine.dispose()
