from __future__ import annotations

import re
from dataclasses import dataclass


DEFAULT_CATEGORY = "Прочее"

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Продукты": ("продукт", "магазин", "супермаркет", "пятерочка", "перекресток", "лента"),
    "Кафе и рестораны": ("кафе", "ресторан", "кофе", "еда", "доставка", "самокат", "вкусвилл"),
    "Транспорт": ("такси", "метро", "автобус", "транспорт", "бензин", "заправка"),
    "Дом": ("дом", "ремонт", "мебель", "коммунал", "жкх", "интернет"),
    "Здоровье": ("аптека", "врач", "клиника", "лекар", "здоров"),
    "Развлечения": ("кино", "театр", "игра", "развлеч", "концерт"),
    "Подписки": ("подписк", "netflix", "spotify", "яндекс", "apple", "google"),
    "Одежда": ("одежд", "обув", "куртка", "футболка"),
    "Дети": ("дет", "садик", "школ", "игруш", "подгуз"),
    "Питомцы": ("кот", "собак", "вет", "корм"),
}

AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:[.,]\d{1,2})?)")


@dataclass(slots=True)
class ParsedExpense:
    amount: float
    category: str
    description: str


def parse_expense(text: str) -> ParsedExpense | None:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return None

    match = AMOUNT_PATTERN.search(normalized)
    if not match:
        return None

    amount = float(match.group("amount").replace(",", "."))
    description = normalized
    category = detect_category(normalized)
    return ParsedExpense(amount=amount, category=category, description=description)


def detect_category(text: str) -> str:
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


def list_categories() -> list[str]:
    return sorted(CATEGORY_KEYWORDS.keys()) + [DEFAULT_CATEGORY]
