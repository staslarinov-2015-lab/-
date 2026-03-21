from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    allowed_chat_id: int | None
    timezone: str = "Europe/Moscow"
    daily_report_hour: int = 21
    daily_report_minute: int = 0
    weekly_report_day: str = "sun"
    weekly_report_hour: int = 20
    weekly_report_minute: int = 0
    monthly_report_day: int = 1
    monthly_report_hour: int = 10
    monthly_report_minute: int = 0


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    allowed_chat_id = os.getenv("ALLOWED_CHAT_ID", "").strip()

    if not bot_token:
        raise ValueError("BOT_TOKEN is required")
    return Settings(
        bot_token=bot_token,
        allowed_chat_id=int(allowed_chat_id) if allowed_chat_id else None,
        timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
        daily_report_hour=int(os.getenv("DAILY_REPORT_HOUR", "21")),
        daily_report_minute=int(os.getenv("DAILY_REPORT_MINUTE", "0")),
        weekly_report_day=os.getenv("WEEKLY_REPORT_DAY", "sun"),
        weekly_report_hour=int(os.getenv("WEEKLY_REPORT_HOUR", "20")),
        weekly_report_minute=int(os.getenv("WEEKLY_REPORT_MINUTE", "0")),
        monthly_report_day=int(os.getenv("MONTHLY_REPORT_DAY", "1")),
        monthly_report_hour=int(os.getenv("MONTHLY_REPORT_HOUR", "10")),
        monthly_report_minute=int(os.getenv("MONTHLY_REPORT_MINUTE", "0")),
    )
