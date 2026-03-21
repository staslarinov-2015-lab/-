from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.categorizer import list_categories, parse_expense
from bot.config import load_settings
from bot.db import ExpenseRepository
from bot.reports import build_report, month_period, today_period, week_period
from bot.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO)

settings = load_settings()
repo = ExpenseRepository()
dp = Dispatcher()


def is_allowed_chat(message: Message) -> bool:
    if settings.allowed_chat_id is None:
        return True
    return message.chat.id == settings.allowed_chat_id


def user_display_name(message: Message) -> str:
    user = message.from_user
    if not user:
        return "Unknown"
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part)
    return full_name or user.username or str(user.id)


async def reject_if_not_allowed(message: Message) -> bool:
    if is_allowed_chat(message):
        return False
    await message.answer("Этот бот настроен только для одного семейного чата.")
    return True


@dp.message(Command("chatid"))
async def cmd_chat_id(message: Message) -> None:
    await message.answer(
        "ID этого чата:\n"
        f"`{message.chat.id}`\n\n"
        "Скопируйте это значение в `ALLOWED_CHAT_ID` в файле `.env`.",
        parse_mode="Markdown",
    )


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await message.answer(
        "Я помогу вести семейные расходы.\n\n"
        "Просто отправьте сообщение вроде `1250 продукты` или `Потратили 890 на такси`.\n"
        "Команды: /today, /week, /month, /categories, /chatid, /help",
        parse_mode="Markdown",
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await message.answer(
        "Как пользоваться:\n"
        "- отправьте сумму и текст траты;\n"
        "- бот сам попробует определить категорию;\n"
        "- для анализа используйте /today, /week, /month.\n\n"
        "Примеры:\n"
        "`450 кофе`\n"
        "`2300 продукты`\n"
        "`Потратили 780 на аптеку`",
        parse_mode="Markdown",
    )


@dp.message(Command("categories"))
async def cmd_categories(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    categories = "\n".join(f"- {category}" for category in list_categories())
    await message.answer(f"Категории:\n{categories}")


@dp.message(Command("today"))
async def cmd_today(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    text = await build_report(repo, chat_id=message.chat.id, period=today_period(settings.timezone))
    await message.answer(text)


@dp.message(Command("week"))
async def cmd_week(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    text = await build_report(repo, chat_id=message.chat.id, period=week_period(settings.timezone))
    await message.answer(text)


@dp.message(Command("month"))
async def cmd_month(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    text = await build_report(repo, chat_id=message.chat.id, period=month_period(settings.timezone))
    await message.answer(text)


@dp.message(F.text)
async def handle_text_expense(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return

    parsed = parse_expense(message.text or "")
    if not parsed:
        await message.answer(
            "Не смог распознать трату. Попробуйте формат вроде `1200 продукты`.",
            parse_mode="Markdown",
        )
        return

    now = datetime.now(ZoneInfo(settings.timezone)).isoformat(timespec="seconds")
    await repo.add_expense(
        chat_id=message.chat.id,
        user_id=message.from_user.id if message.from_user else None,
        user_name=user_display_name(message),
        amount=parsed.amount,
        category=parsed.category,
        description=parsed.description,
        created_at=now,
    )
    await message.answer(
        f"Сохранил расход: {parsed.amount:.2f}\nКатегория: {parsed.category}\nОписание: {parsed.description}"
    )


async def main() -> None:
    await repo.init()
    bot = Bot(token=settings.bot_token)
    scheduler = build_scheduler(bot=bot, repo=repo, settings=settings)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        await scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
