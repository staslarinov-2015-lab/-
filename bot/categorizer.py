from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

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
        "окей",
        "okey",
        "кб",
        "к б",
        "красное белое",
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
        "перекус",
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
        "троллейбус",
        "трамвай",
        "маршрутка",
        "маршрутное такси",
        "мцк",
        "мцд",
        "аэроэкспресс",
        "проездной",
        "тройка",
        "подорожник",
        "электрич",
        "поезд",
        "ржд",
        "жд",
        "транспорт",
        "каршер",
        "бензин",
        "заправка",
        "азс",
        "парковк",
        "авто",
        "то",
        "т о",
        "техобслуж",
        "тех обслуживание",
        "обслуживание авто",
        "автосервис",
        "сервис авто",
        "шиномонтаж",
        "мойка",
        "масло",
        "осаго",
        "каско",
        "ремонт авто",
    ),
    "Дом": (
        "дом",
        "ремонт",
        "мебель",
        "икеа",
        "hoff",
        "леруа",
        "leroy",
        "obi",
        "коммунал",
        "жкх",
        "квартплат",
        "аренда",
        "квартира",
        "интернет",
        "вайфай",
        "wi fi",
        "роутер",
        "свет",
        "вода",
        "газ",
        "хозтовар",
        "порошок",
        "бытовая химия",
        "моющее",
        "посуда",
        "сковород",
        "лампочка",
        "пылесос",
        "чайник",
        "матрас",
        "подушка",
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
        "укол",
        "мрт",
        "кт",
        "узи",
        "рентген",
        "психолог",
        "массаж",
        "витамин",
        "медосмотр",
        "страховка",
        "полис",
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
        "сбермаркет",
        "казаньэкспресс",
        "joom",
        "temu",
        "amazon",
        "ebay",
    ),
    "Дети": (
        "дет",
        "ребен",
        "сын",
        "дочь",
        "садик",
        "школ",
        "игруш",
        "подгуз",
        "кружок",
        "секция",
        "учебник",
        "канцтовар",
        "тетрад",
        "рюкзак",
        "коляска",
        "смесь",
        "питание ребенку",
    ),
    "Питомцы": ("кот", "кошка", "собак", "вет", "ветеринар", "корм", "зоомагаз"),
}

AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:[.,]\d{1,2})?)")


@dataclass(slots=True)
class ParsedExpense:
    amount: float
    category: str
    description: str
    matched_keywords: tuple[str, ...]


@dataclass(slots=True)
class ParseExpensesResult:
    expenses: list[ParsedExpense]
    error: str | None = None


@dataclass(slots=True)
class ParsedMessage:
    expenses: list[ParsedExpense]
    expense_date: date | None
    error: str | None = None


def parse_expense(text: str) -> ParsedExpense | None:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return None

    match = AMOUNT_PATTERN.search(normalized)
    if not match:
        return None

    amount = float(match.group("amount").replace(",", "."))
    description = normalized
    category_match = detect_category(normalized)
    if category_match is None:
        return None

    category, matched_keywords = category_match
    return ParsedExpense(
        amount=amount,
        category=category,
        description=description,
        matched_keywords=matched_keywords,
    )


def parse_expenses(text: str) -> ParseExpensesResult:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return ParseExpensesResult(expenses=[], error="Сообщение пустое.")

    matches = list(AMOUNT_PATTERN.finditer(normalized))
    if not matches:
        return ParseExpensesResult(
            expenses=[],
            error="Не нашел ни одной суммы. Попробуйте формат вроде `1200 продукты`.",
        )

    if len(matches) == 1:
        parsed = parse_expense(normalized)
        if parsed is None:
            return ParseExpensesResult(
                expenses=[],
                error=(
                    "Не нашел ни одной категории в сообщении. Попробуйте написать трату с "
                    "понятным ключевым словом, например `1200 продукты`, `450 такси` или `780 аптека`."
                ),
            )
        return ParseExpensesResult(expenses=[parsed])

    parsed_expenses: list[ParsedExpense] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        chunk = normalized[start:end].strip(" ,;")
        parsed = parse_expense(chunk)
        if parsed is None:
            return ParseExpensesResult(
                expenses=[],
                error=(
                    "Не смог разобрать одну из трат в сообщении. "
                    "Пишите блоками вида `178 перекус 65 вода 335 обед`."
                ),
            )
        parsed_expenses.append(parsed)

    return ParseExpensesResult(expenses=parsed_expenses)


def parse_message(text: str, *, today: date | None = None) -> ParsedMessage:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return ParsedMessage(expenses=[], expense_date=None, error="Сообщение пустое.")

    expense_date, cleaned_text = extract_expense_date(normalized, today=today)
    parsed_result = parse_expenses(cleaned_text)
    return ParsedMessage(
        expenses=parsed_result.expenses,
        expense_date=expense_date,
        error=parsed_result.error,
    )


def detect_category(text: str) -> tuple[str, tuple[str, ...]] | None:
    lowered = normalize_text(text)
    for category, keywords in CATEGORY_KEYWORDS.items():
        matched_keywords = tuple(keyword for keyword in keywords if keyword_matches(lowered, keyword))
        if matched_keywords:
            return category, matched_keywords
    return None


def list_categories() -> list[str]:
    return sorted(CATEGORY_KEYWORDS.keys())


def normalize_text(text: str) -> str:
    lowered = text.lower().replace("ё", "е")
    # Normalization improves matching for common shorthand and marketplace names.
    lowered = re.sub(r"[^\w\s]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def keyword_matches(text: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)

    # Short keywords and full phrases should match as whole words,
    # otherwise tokens like "то" would fire inside unrelated words.
    if len(normalized_keyword) <= 2 or " " in normalized_keyword:
        pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"
        return re.search(pattern, text) is not None

    return normalized_keyword in text


def extract_expense_date(text: str, *, today: date | None = None) -> tuple[date | None, str]:
    today = today or datetime.now().date()
    normalized = text.strip()
    lowered = normalize_text(normalized)

    relative_patterns = {
        "сегодня": today,
        "вчера": today - timedelta(days=1),
        "позавчера": today - timedelta(days=2),
    }
    for prefix, parsed_date in relative_patterns.items():
        if lowered == prefix:
            return parsed_date, ""
        if lowered.startswith(f"{prefix} "):
            return parsed_date, normalized[len(prefix):].strip()

    iso_match = re.match(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(?:\s+|$)", normalized)
    if iso_match:
        parsed_date = date(
            int(iso_match.group("year")),
            int(iso_match.group("month")),
            int(iso_match.group("day")),
        )
        return parsed_date, normalized[iso_match.end():].strip()

    ru_match = re.match(r"^(?P<day>\d{1,2})\.(?P<month>\d{1,2})(?:\.(?P<year>\d{4}))?(?:\s+|$)", normalized)
    if ru_match:
        parsed_year = int(ru_match.group("year")) if ru_match.group("year") else today.year
        parsed_date = date(
            parsed_year,
            int(ru_match.group("month")),
            int(ru_match.group("day")),
        )
        return parsed_date, normalized[ru_match.end():].strip()

    return None, normalized
