from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.db import ExpenseRepository


@dataclass(slots=True)
class Period:
    label: str
    start: datetime
    end: datetime


def today_period(tz_name: str) -> Period:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return Period(label="Сегодня", start=start, end=end)


def week_period(tz_name: str) -> Period:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(seconds=1)
    return Period(label="Последние 7 дней", start=start, end=end)


def month_period(tz_name: str) -> Period:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return Period(label="Текущий месяц", start=start, end=end)


async def build_report(repo: ExpenseRepository, *, chat_id: int, period: Period) -> str:
    expenses = await repo.fetch_expenses_between(
        chat_id=chat_id,
        start_iso=period.start.isoformat(),
        end_iso=period.end.isoformat(),
    )
    if not expenses:
        return f"{period.label}\n\nРасходов пока нет."

    total = sum(item["amount"] for item in expenses)
    by_category: dict[str, float] = defaultdict(float)
    by_user: dict[str, float] = defaultdict(float)
    for item in expenses:
        by_category[item["category"]] += item["amount"]
        by_user[item["user_name"] or "Неизвестно"] += item["amount"]

    top_categories = sorted(by_category.items(), key=lambda item: item[1], reverse=True)[:5]
    top_users = sorted(by_user.items(), key=lambda item: item[1], reverse=True)
    average = total / max(len(expenses), 1)

    lines = [
        period.label,
        "",
        f"Всего расходов: {total:.2f}",
        f"Операций: {len(expenses)}",
        f"Средний чек: {average:.2f}",
        "",
        "Топ категорий:",
    ]

    lines.extend(f"- {category}: {amount:.2f}" for category, amount in top_categories)

    lines.append("")
    lines.append("По участникам:")
    lines.extend(f"- {user}: {amount:.2f}" for user, amount in top_users)

    latest_items = expenses[:5]
    lines.append("")
    lines.append("Последние траты:")
    lines.extend(
        f"- {item['created_at'][11:16]} | {item['amount']:.2f} | {item['category']} | {item['description']}"
        for item in latest_items
    )
    return "\n".join(lines)
