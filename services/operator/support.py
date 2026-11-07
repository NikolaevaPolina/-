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
    opening = f"Здравствуйте! Ваше обращение «{title}» принято в работу."
    note = specialist_note.casefold()
    # Замечание о преждевременном решении отменяет обещания и технические выводы.
    if any(phrase in note for phrase in (
        "взята в работу", "взято в работу", "принята в работу", "принято в работу",
        "не говори", "не писать", "не пиши", "не решен", "не решён",
        "после исправления", "только статус", "проблема взята в работу",
    )):
        return opening
    checks = {
        "Не отправляется письмо": "Проверим почтовый ящик и отправку сообщений.",
        "Создание группы рассылки": "Проверим параметры группы и права на её изменение.",
        "Настройка почтового клиента": "Проверим настройки клиента и подключение к почте.",
        "Не подключается VPN": "Проверим подключение и параметры удалённого доступа.",
        "Истёк сертификат": "Проверим срок действия сертификата.",
        "Медленное соединение": "Проверим качество соединения.",
        "Сброс пароля": "Проверим учётную запись и порядок восстановления доступа.",
        "Блокировка учётной записи": "Проверим причину блокировки.",
        "Предоставление доступа": "Проверим необходимые согласования и права доступа.",
        "Не включается компьютер": "Проверим питание и состояние оборудования.",
        "Установка программы": "Проверим возможность установки и необходимые права.",
        "Не работает периферия": "Проверим подключение и состояние устройства.",
        "Ошибка при входе": "Проверим доступ к системе и причину ошибки.",
        "Не формируется отчёт": "Проверим параметры отчёта и работу системы.",
        "Недоступен сервис": "Проверим доступность сервиса и состояние подключения.",
    }
    return f"{opening} {checks.get(title, 'Проверим обстоятельства обращения.')}"
