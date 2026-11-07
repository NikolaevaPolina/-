"""Модель подбора ответа по решениям, согласованным специалистом."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


MIN_EXAMPLES = 3


class FeedbackReplyModel:
    def __init__(self, examples: Sequence[Mapping]):
        self.examples = [
            row for row in examples
            if row.get("edited_reply") and str(row["edited_reply"]).strip()
        ]
        self.vectorizer = None
        self.matrix = None
        if len(self.examples) >= MIN_EXAMPLES:
            self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=1)
            self.matrix = self.vectorizer.fit_transform([self._text(row) for row in self.examples])

    @staticmethod
    def _text(row: Mapping) -> str:
        return f"{row.get('title', '')} {row.get('review_note', '')}"

    @property
    def ready(self) -> bool:
        return self.matrix is not None

    def recommend(self, title: str, note: str = "") -> tuple[str | None, float]:
        if not self.ready:
            return None, 0.0
        query = self.vectorizer.transform([f"{title} {note}"])
        scores = cosine_similarity(query, self.matrix)[0]
        index = int(scores.argmax())
        return str(self.examples[index]["edited_reply"]), float(scores[index])
