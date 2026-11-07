"""Поиск похожих заявок и подготовка текста для проверки специалистом.

Оценка сходства отражает совпадение слов в синтетических темах.
Она не показывает вероятность решения новой заявки.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence


def title_words(value: str) -> set[str]:
    return set(re.findall(r"[а-яёa-z0-9]+", value.casefold()))


def similarity_score(current: Mapping, candidate: Mapping, category: str | None) -> float:
    # Сходство темы имеет больший вес; сервис и категория уточняют порядок выдачи.
    current_words = title_words(str(current["title"]))
    past_words = title_words(str(candidate["title"]))
    union = current_words | past_words
    overlap = len(current_words & past_words) / len(union) if union else 0.0
    service_match = current.get("service") == candidate.get("service")
    category_match = bool(category) and category == candidate.get("category")
    return round(0.8 * overlap + 0.1 * service_match + 0.1 * category_match, 4)


def rank_candidates(
    current: Mapping, candidates: Sequence[Mapping], category: str | None, limit: int = 3
) -> list[dict]:
    ranked = [
        {**candidate, "similarity": similarity_score(current, candidate, category)}
        for candidate in candidates
    ]
    ranked.sort(key=lambda row: (-row["similarity"], -int(row["ticket_id"])))
    return ranked[:limit]


def build_draft(
    current: Mapping,
    reference: Mapping | None,
    specialist_note: str = "",
) -> str:
    """Составить текст рекомендации без утверждения, что заявка уже решена."""
    title = str(current["title"]).strip()
    service = str(current.get("service", "службы поддержки")).strip()
    issue = title.lower()
    service_actions = {
        "Корпоративная почта": "проверим настройки почтового ящика и состояние почтового сервиса",
        "Удалённый доступ": "проверим подключение, сертификат и параметры удалённого доступа",
        "Учётные записи": "проверим состояние учётной записи и необходимые права доступа",
        "Рабочее место": "проверим оборудование и установленное программное обеспечение",
        "Корпоративные системы": "проверим доступность системы и журналы работы приложения",
    }
    action = service_actions.get(service, "проведём диагностику сервиса")
    if reference is None:
        draft = (
            f"Здравствуйте! Получили ваше обращение «{title}». "
            f"По вопросу «{issue}» {action}. "
            "Сообщим результат после проверки."
        )
    else:
        past_resolution = str(reference["resolution_text"]).strip()
        draft = (
            f"Здравствуйте! Получили ваше обращение «{title}». "
            f"В похожем ранее решённом случае применялось следующее решение: {past_resolution} "
            f"Для обращения «{issue}» {action}. "
            "Проверим, подходит ли оно для вашего обращения, и сообщим результат."
        )
    note = specialist_note.strip()
    if note:
        draft += f" Учтём дополнительное указание специалиста: {note}."
    return draft

