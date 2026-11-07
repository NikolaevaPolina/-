"""Подготовка проекта ответа локальной языковой моделью."""

from __future__ import annotations

import json
import os
from urllib import error, request


class ReplyModelError(RuntimeError):
    pass


class ReplyModel:
    def __init__(self):
        self.url = os.getenv("REPLY_MODEL_URL", "http://reply-model:11434/api/chat")
        self.name = os.getenv("REPLY_MODEL_NAME", "qwen2.5:3b")

    def revise(self, title: str, description: str, draft: str, note: str) -> str:
        if not note.strip():
            raise ValueError("Замечание не заполнено")
        payload = {
            "model": self.name,
            "stream": False,
            "options": {"temperature": 0.15, "num_predict": 220},
            "messages": [
                {"role": "system", "content": (
                    "Ты составляешь только текст ответа заявителю службы технической поддержки на русском языке. "
                    "Следуй замечанию специалиста при изменении черновика. "
                    "Не сообщай, что проблема уже решена, если это неизвестно. "
                    "Не упоминай прошлые заявки, нейросеть, черновик или замечание. "
                    "Не добавляй сведения о пользователе, которых нет во входных данных. "
                    "Верни только готовый текст ответа без пояснений."
                )},
                {"role": "user", "content": (
                    f"Тема заявки: {title}\nОписание: {description}\n"
                    f"Текущий черновик: {draft}\nЗамечание специалиста: {note}\n"
                    "Перепиши черновик с учётом замечания."
                )},
            ],
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            req = request.Request(self.url, body, {"Content-Type": "application/json"})
            with request.urlopen(req, timeout=120) as response:
                result = json.load(response)
        except (OSError, error.HTTPError, ValueError) as exc:
            raise ReplyModelError("Локальная модель недоступна") from exc
        text = str(result.get("message", {}).get("content", "")).strip()
        if not text or len(text) > 2500:
            raise ReplyModelError("Локальная модель вернула некорректный ответ")
        return text
