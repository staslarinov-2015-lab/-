from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.config import Settings
from bot.db import ExpenseRepository
from bot.reports import build_report, month_period, today_period, week_period

ReportSender = Callable[[], Awaitable[None]]

WEEKDAY_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


class ReportScheduler:
    def __init__(self, *, bot, repo: ExpenseRepository, settings: Settings) -> None:
        self.bot = bot
        self.repo = repo
        self.settings = settings
        self._tasks: list[asyncio.Task] = []

    def start(self) -> None:
        if self.settings.allowed_chat_id is None:
            return

        self._tasks = [
            asyncio.create_task(
                self._run_daily(
                    self._send_daily_report,
                    hour=self.settings.daily_report_hour,
                    minute=self.settings.daily_report_minute,
                )
            ),
            asyncio.create_task(
                self._run_weekly(
                    self._send_weekly_report,
                    weekday=WEEKDAY_MAP[self.settings.weekly_report_day.lower()],
                    hour=self.settings.weekly_report_hour,
                    minute=self.settings.weekly_report_minute,
                )
            ),
            asyncio.create_task(
                self._run_monthly(
                    self._send_monthly_report,
                    day=self.settings.monthly_report_day,
                    hour=self.settings.monthly_report_hour,
                    minute=self.settings.monthly_report_minute,
                )
            ),
        ]

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _send_daily_report(self) -> None:
        text = await build_report(
            self.repo,
            chat_id=self.settings.allowed_chat_id,
            period=today_period(self.settings.timezone),
        )
        await self.bot.send_message(self.settings.allowed_chat_id, f"Ежедневная сводка\n\n{text}")

    async def _send_weekly_report(self) -> None:
        text = await build_report(
            self.repo,
            chat_id=self.settings.allowed_chat_id,
            period=week_period(self.settings.timezone),
        )
        await self.bot.send_message(self.settings.allowed_chat_id, f"Еженедельная сводка\n\n{text}")

    async def _send_monthly_report(self) -> None:
        text = await build_report(
            self.repo,
            chat_id=self.settings.allowed_chat_id,
            period=month_period(self.settings.timezone),
        )
        await self.bot.send_message(self.settings.allowed_chat_id, f"Ежемесячная сводка\n\n{text}")

    async def _run_daily(self, sender: ReportSender, *, hour: int, minute: int) -> None:
        while True:
            await asyncio.sleep(self._seconds_until_daily(hour=hour, minute=minute))
            await sender()

    async def _run_weekly(self, sender: ReportSender, *, weekday: int, hour: int, minute: int) -> None:
        while True:
            await asyncio.sleep(self._seconds_until_weekly(weekday=weekday, hour=hour, minute=minute))
            await sender()

    async def _run_monthly(self, sender: ReportSender, *, day: int, hour: int, minute: int) -> None:
        while True:
            await asyncio.sleep(self._seconds_until_monthly(day=day, hour=hour, minute=minute))
            await sender()

    def _seconds_until_daily(self, *, hour: int, minute: int) -> float:
        tz = ZoneInfo(self.settings.timezone)
        now = datetime.now(tz)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return (target - now).total_seconds()

    def _seconds_until_weekly(self, *, weekday: int, hour: int, minute: int) -> float:
        tz = ZoneInfo(self.settings.timezone)
        now = datetime.now(tz)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = (weekday - now.weekday()) % 7
        target += timedelta(days=days_ahead)
        if target <= now:
            target += timedelta(days=7)
        return (target - now).total_seconds()

    def _seconds_until_monthly(self, *, day: int, hour: int, minute: int) -> float:
        tz = ZoneInfo(self.settings.timezone)
        now = datetime.now(tz)
        target = self._build_monthly_target(now=now, day=day, hour=hour, minute=minute)
        if target <= now:
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            target = self._build_monthly_target(now=next_month, day=day, hour=hour, minute=minute)
        return (target - now).total_seconds()

    @staticmethod
    def _build_monthly_target(*, now: datetime, day: int, hour: int, minute: int) -> datetime:
        if now.month == 12:
            next_month_start = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month_start = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = (next_month_start - timedelta(days=1)).day
        safe_day = min(day, last_day)
        return now.replace(day=safe_day, hour=hour, minute=minute, second=0, microsecond=0)


def build_scheduler(*, bot, repo: ExpenseRepository, settings: Settings) -> ReportScheduler:
    return ReportScheduler(bot=bot, repo=repo, settings=settings)
