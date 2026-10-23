from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base

# SQLite va PostgreSQL uchun universal Primary Key tipi
# SQLite'da INTEGER PRIMARY KEY avtomatik 64-bit autoincrement bo'ladi
PK_BIGINT = BigInteger().with_variant(Integer, "sqlite")
PK_INT = Integer().with_variant(Integer, "sqlite")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} full_name={self.full_name}>"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(PK_INT, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Admin id={self.id} telegram_id={self.telegram_id} username={self.username} phone={self.phone_number}>"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(PK_INT, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    pdf_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title} author={self.author}>"
