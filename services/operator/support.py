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
    note = specialist_note.casefold()
    title_visible = not any(phrase in note for phrase in ("не пиши название", "не указывай название", "убери название"))
    opening = "Здравствуйте!"
    if title_visible:
        opening += f" Ваше обращение «{title}» принято в работу."
    else:
        opening += " Обращение принято в работу."
    if "почтов" in note and any(word in note for word in ("верс", "клиент")):
        return (
            f"{opening} Уточните, пожалуйста, каким почтовым клиентом вы пользуетесь "
            "и какая у него версия. Пока проверяем настройки подключения к почте."
        )
    if any(word in note for word in ("роль", "этап", "шаге", "на каком шаге")) and "групп" in note:
        return (
            "Здравствуйте! Чтобы разобраться с созданием группы рассылки, уточните, "
            "пожалуйста, какая у вас роль в системе и на каком этапе возникает проблема."
        )
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
    sentence = checks.get(title, "Проверяем обстоятельства обращения.")
    if sentence.startswith("Проверим"):
        sentence = sentence.replace("Проверим", "Проверяем", 1)
    if any(phrase in note for phrase in ("добавь шаги", "добавить шаги", "шаги, которые", "что могут помочь")):
        steps = {
            "Не работает периферия": "Проверьте, плотно ли подключён кабель. Если есть возможность, подключите устройство к другому разъёму и проверьте его на другом компьютере.",
            "Не включается компьютер": "Проверьте подключение кабеля питания и включён ли сетевой фильтр. Если компьютер подключён к нему, попробуйте другую розетку.",
        }
        sentence += " " + steps.get(title, "Пожалуйста, проверьте подключение устройства и повторите действие. Если ошибка останется, сообщите нам.")
    return f"{opening} {sentence}"
