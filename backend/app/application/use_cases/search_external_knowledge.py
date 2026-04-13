from __future__ import annotations

from datetime import datetime
from typing import Any

from app.infrastructure.learning.repository import LearningArchiveMongoRepository
from app.infrastructure.learning.schemas import ExternalKnowledgeSearchQuery


class SearchExternalKnowledgeUseCase:
    def __init__(self, repository: LearningArchiveMongoRepository) -> None:
        self.repository = repository

    async def execute(self, query: ExternalKnowledgeSearchQuery) -> list[dict]:
        candidate_limit = max(20, min(200, query.limit * 5))
        candidates = await self.repository.search_external_knowledge(
            query_text=query.query,
            source_name=query.source_name,
            language=query.language,
            framework=query.framework,
            vulnerability_category=query.vulnerability_category,
            weakness_id=query.weakness_id,
            tags=query.tags,
            limit=candidate_limit,
            offset=0,
        )
        scored = [self._score_item(item, query) for item in candidates]
        scored.sort(
            key=lambda item: (
                -float(item.get("retrieval_score", 0.0)),
                -_timestamp_sort_key(item.get("updated_at")),
            )
        )
        start = max(0, int(query.offset))
        end = start + max(1, min(int(query.limit), 100))
        return scored[start:end]

    def _score_item(self, item: dict[str, Any], query: ExternalKnowledgeSearchQuery) -> dict[str, Any]:
        score = 0.0
        query_text = query.query.strip().lower()
        title = str(item.get("title") or "").strip().lower()
        summary = str(item.get("summary") or "").strip().lower()
        retrieval_text = str(item.get("retrieval_text") or "").strip().lower()
        tags = {str(tag).strip().lower() for tag in (item.get("tags") or [])}

        if query_text:
            if title == query_text:
                score += 10.0
            elif title.startswith(query_text):
                score += 7.5
            if query_text in title:
                score += 5.0
            if query_text in summary:
                score += 3.0
            if query_text in retrieval_text:
                score += 2.0
            for token in [token for token in query_text.split(" ") if token]:
                if token in title:
                    score += 1.5
                elif token in retrieval_text:
                    score += 0.5

        if query.language and str(item.get("language") or "").strip().lower() == query.language.strip().lower():
            score += 2.0
        if query.framework and str(item.get("framework") or "").strip().lower() == query.framework.strip().lower():
            score += 2.0
        if query.vulnerability_category and str(item.get("vulnerability_category") or "").strip().lower() == query.vulnerability_category.strip().lower():
            score += 2.0
        if query.source_name and str(item.get("source_name") or "").strip().lower() == query.source_name.strip().lower():
            score += 1.0
        if query.weakness_id and str(item.get("weakness_id") or "").strip().upper() == query.weakness_id.strip().upper():
            score += 2.0
        if query.tags:
            wanted_tags = {tag.strip().lower() for tag in query.tags if tag.strip()}
            intersection = wanted_tags & tags
            if intersection:
                score += 1.5 * len(intersection)

        enriched = dict(item)
        enriched["retrieval_score"] = round(score, 4)
        return enriched


def _timestamp_sort_key(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    return 0.0
