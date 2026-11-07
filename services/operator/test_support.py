"""Проверки сортировки похожих заявок и текста рекомендации."""

import unittest

from support import build_draft, rank_candidates


class SupportTests(unittest.TestCase):
    def test_same_title_ranks_first(self):
        current = {"title": "Не отправляется письмо", "service": "Почта"}
        candidates = [
            {"ticket_id": 1, "title": "Сброс пароля", "service": "Почта", "category": "Почта"},
            {"ticket_id": 2, "title": "Не отправляется письмо", "service": "Почта", "category": "Почта"},
        ]
        ranked = rank_candidates(current, candidates, "Почта")
        self.assertEqual(ranked[0]["ticket_id"], 2)
        self.assertGreater(ranked[0]["similarity"], ranked[1]["similarity"])

    def test_rejection_changes_customer_reply_without_exposing_reference(self):
        current = {"title": "Не включается компьютер"}
        reference = {"resolution_text": "Работа сервиса восстановлена."}
        initial = build_draft(current, reference)
        revised = build_draft(current, reference, "Не говори, что нашли решение. Проблема взята в работу.")
        self.assertIn("Проверим питание", initial)
        self.assertIn("принято в работу", revised)
        self.assertNotIn("Проверим питание", revised)
        self.assertNotIn("ранее решённом", revised)
        self.assertNotIn("Работа сервиса восстановлена", revised)


if __name__ == "__main__":
    unittest.main()
