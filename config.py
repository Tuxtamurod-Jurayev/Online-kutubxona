import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    ADMIN_IDS: str = ""  # Masalan: "12345678,87654321"
    DATABASE_URL: str = "sqlite+aiosqlite:///bot.db"
    RATE_LIMIT: float = 1.0  # Sekundiga xabar chegarasi

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_id_list(self) -> List[int]:
        """ADMIN_IDS satrini integer ro'yxatiga aylantirish"""
        if not self.ADMIN_IDS.strip():
            return []
        ids = []
        for x in self.ADMIN_IDS.split(","):
            cleaned = x.strip()
            if cleaned.isdigit():
                ids.append(int(cleaned))
        return ids


config = Settings()
