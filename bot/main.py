from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from bot.categorizer import list_categories, parse_message
from bot.config import load_settings
from bot.db import ExpenseRepository
from bot.reports import build_report, month_period, today_period, week_period
from bot.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO)

settings = load_settings()
repo = ExpenseRepository()
dp = Dispatcher()

DAILY_REPORT_BUTTON = "Отчет за день"
WEEKLY_REPORT_BUTTON = "Отчет за неделю"


def is_allowed_chat(message: Message) -> bool:
    if settings.allowed_chat_id is None:
        return True
    return message.chat.id == settings.allowed_chat_id


def user_display_name(message: Message) -> str:
    user = message.from_user
    if not user:
        return "Unknown"
    candidates = [
        user.first_name or "",
        user.last_name or "",
        " ".join(part for part in [user.first_name, user.last_name] if part),
        user.username or "",
    ]

    normalized_candidates = [normalize_person_name(candidate) for candidate in candidates if candidate]
    if any(alias in candidate for candidate in normalized_candidates for alias in settings.stas_aliases):
        return "Стас"
    if any(alias in candidate for candidate in normalized_candidates for alias in settings.kristina_aliases):
        return "Кристина"

    full_name = " ".join(part for part in [user.first_name, user.last_name] if part)
    return full_name or user.username or str(user.id)


def normalize_person_name(value: str) -> str:
    return value.strip().lower().replace("ё", "е")


async def reject_if_not_allowed(message: Message) -> bool:
    if is_allowed_chat(message):
        return False
    await message.answer("Этот бот настроен только для одного семейного чата.")
    return True


def reports_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DAILY_REPORT_BUTTON), KeyboardButton(text=WEEKLY_REPORT_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Введите трату или нажмите кнопку отчета",
    )


async def send_today_report(message: Message) -> None:
    text = await build_report(repo, chat_id=message.chat.id, period=today_period(settings.timezone))
    await message.answer(text, reply_markup=reports_keyboard())


async def send_week_report(message: Message) -> None:
    text = await build_report(repo, chat_id=message.chat.id, period=week_period(settings.timezone))
    await message.answer(text, reply_markup=reports_keyboard())


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
        "Команды: /today, /week, /month, /categories, /chatid, /help\n"
        "Или используйте кнопки для быстрых отчетов.",
        parse_mode="Markdown",
        reply_markup=reports_keyboard(),
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await message.answer(
        "Как пользоваться:\n"
        "- отправьте сумму и текст траты;\n"
        "- можно указать дату в начале сообщения;\n"
        "- можно отправлять несколько трат в одном сообщении;\n"
        "- бот сам попробует определить категорию;\n"
        "- для анализа используйте /today, /week, /month.\n\n"
        "Примеры:\n"
        "`450 кофе`\n"
        "`21.03 2300 продукты`\n"
        "`вчера 780 аптека`\n"
        "`2300 продукты`\n"
        "`Потратили 780 на аптеку`\n"
        "`178 перекус 65 вода 335 обед`",
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
    await send_today_report(message)


@dp.message(Command("week"))
async def cmd_week(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await send_week_report(message)


@dp.message(Command("month"))
async def cmd_month(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    text = await build_report(repo, chat_id=message.chat.id, period=month_period(settings.timezone))
    await message.answer(text, reply_markup=reports_keyboard())


@dp.message(F.text == DAILY_REPORT_BUTTON)
async def button_today_report(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await send_today_report(message)


@dp.message(F.text == WEEKLY_REPORT_BUTTON)
async def button_week_report(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await send_week_report(message)


@dp.message(F.text)
async def handle_text_expense(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return

    parsed_message = parse_message(message.text or "", today=datetime.now(ZoneInfo(settings.timezone)).date())
    if parsed_message.error:
        await message.answer(
            parsed_message.error,
            parse_mode="Markdown",
            reply_markup=reports_keyboard(),
        )
        return

    now_dt = datetime.now(ZoneInfo(settings.timezone))
    if parsed_message.expense_date is None:
        created_at = now_dt.isoformat(timespec="seconds")
    else:
        created_at = datetime.combine(
            parsed_message.expense_date,
            now_dt.timetz().replace(microsecond=0),
        ).isoformat()

    for parsed in parsed_message.expenses:
        await repo.add_expense(
            chat_id=message.chat.id,
            user_id=message.from_user.id if message.from_user else None,
            user_name=user_display_name(message),
            amount=parsed.amount,
            category=parsed.category,
            description=parsed.description,
            created_at=created_at,
        )

    date_note = ""
    if parsed_message.expense_date is not None:
        date_note = f"\nДата: {parsed_message.expense_date.strftime('%d.%m.%Y')}"

    if len(parsed_message.expenses) == 1:
        parsed = parsed_message.expenses[0]
        await message.answer(
            "Сохранил расход: "
            f"{parsed.amount:.2f}\n"
            f"Категория: {parsed.category}\n"
            f"Ключевые слова: {', '.join(parsed.matched_keywords)}\n"
            f"Описание: {parsed.description}"
            f"{date_note}",
            reply_markup=reports_keyboard(),
        )
        return

    lines = [f"Сохранил {len(parsed_message.expenses)} трат:"]
    if parsed_message.expense_date is not None:
        lines.append(f"Дата: {parsed_message.expense_date.strftime('%d.%m.%Y')}")
    lines.extend(
        f"- {parsed.amount:.2f} | {parsed.category} | {parsed.description}"
        for parsed in parsed_message.expenses
    )
    await message.answer("\n".join(lines), reply_markup=reports_keyboard())


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
