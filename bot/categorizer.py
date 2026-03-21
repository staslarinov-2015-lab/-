from __future__ import annotations

import re
from dataclasses import dataclass


DEFAULT_CATEGORY = "Прочее"

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Продукты": (
        "продукт",
        "еда домой",
        "магазин",
        "супермаркет",
        "гипермаркет",
        "пятерочка",
        "перекресток",
        "лента",
        "ашан",
        "магнит",
        "дикси",
        "верный",
        "спар",
        "spar",
        "вкусвилл",
        "фермер",
    ),
    "Кафе и рестораны": (
        "кафе",
        "ресторан",
        "кофе",
        "капучино",
        "латте",
        "пицца",
        "бургер",
        "суши",
        "роллы",
        "обед",
        "ужин",
        "завтрак",
        "доставка",
        "самокат",
        "яндекс еда",
        "delivery",
        "deliv",
        "delivery club",
    ),
    "Транспорт": (
        "такси",
        "яндекс go",
        "uber",
        "метро",
        "автобус",
        "электрич",
        "поезд",
        "транспорт",
        "каршер",
        "бензин",
        "заправка",
        "азс",
        "парковк",
        "авто",
    ),
    "Дом": (
        "дом",
        "ремонт",
        "мебель",
        "икеа",
        "коммунал",
        "жкх",
        "квартплат",
        "аренда",
        "квартира",
        "интернет",
        "свет",
        "вода",
        "газ",
        "хозтовар",
    ),
    "Здоровье": (
        "аптека",
        "врач",
        "клиника",
        "анализ",
        "стомат",
        "дантист",
        "лекар",
        "таблет",
        "здоров",
    ),
    "Развлечения": (
        "кино",
        "театр",
        "игра",
        "развлеч",
        "концерт",
        "музей",
        "парк",
        "бар",
        "клуб",
        "отдых",
    ),
    "Подписки": (
        "подписк",
        "netflix",
        "spotify",
        "youtube premium",
        "telegram premium",
        "яндекс плюс",
        "apple",
        "icloud",
        "google",
        "google one",
    ),
    "Одежда": (
        "одежд",
        "обув",
        "куртка",
        "футболка",
        "джинс",
        "кофта",
        "кроссов",
        "ботинки",
        "wb",
        "wildberries",
        "lamoda",
    ),
    "Маркетплейсы": (
        "ozon",
        "озон",
        "маркетплейс",
        "яндекс маркет",
        "мегамаркет",
        "алиэкспресс",
        "aliexpress",
    ),
    "Дети": ("дет", "садик", "школ", "игруш", "подгуз", "кружок"),
    "Питомцы": ("кот", "кошка", "собак", "вет", "ветеринар", "корм", "зоомагаз"),
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
    lowered = normalize_text(text)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


def list_categories() -> list[str]:
    return sorted(CATEGORY_KEYWORDS.keys()) + [DEFAULT_CATEGORY]


def normalize_text(text: str) -> str:
    lowered = text.lower().replace("ё", "е")
    # Normalization improves matching for common shorthand and marketplace names.
    lowered = re.sub(r"[^\w\s]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered
