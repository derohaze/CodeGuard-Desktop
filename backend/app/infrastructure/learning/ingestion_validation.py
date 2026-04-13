from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from app.infrastructure.learning.schemas import ExternalKnowledgeSourceSpec


MAX_TEXT_FIELD_LENGTH = 64_000
MAX_TAGS = 32
MAX_TAG_LENGTH = 64


@dataclass(slots=True, frozen=True)
class SanitizedExternalItem:
    item: dict[str, Any]


def validate_external_source_spec(source: ExternalKnowledgeSourceSpec) -> None:
    source_name = source.source_name.strip()
    source_version = source.source_version.strip()
    item_type = source.item_type.strip()
    if not source_name:
        raise ValueError("source_name must not be empty.")
    if not source_version:
        raise ValueError("source_version must not be empty.")
    if not item_type:
        raise ValueError("item_type must not be empty.")
    _validate_endpoint(source.endpoint)


def sanitize_external_item(raw_item: dict[str, Any]) -> SanitizedExternalItem:
    if not isinstance(raw_item, dict):
        raise ValueError("External item must be an object.")

    sanitized: dict[str, Any] = {}
    for key, value in raw_item.items():
        normalized_key = str(key).strip()
        if not normalized_key:
            continue
        if isinstance(value, str):
            sanitized[normalized_key] = _sanitize_text(value)
        elif isinstance(value, list):
            sanitized[normalized_key] = _sanitize_list(value)
        elif isinstance(value, dict):
            sanitized[normalized_key] = _sanitize_dict(value)
        else:
            sanitized[normalized_key] = value

    title = str(sanitized.get("title") or "").strip()
    summary = str(sanitized.get("summary") or sanitized.get("description") or "").strip()
    if not title and not summary:
        raise ValueError("External item must include a non-empty title or summary.")

    tags = sanitized.get("tags")
    if isinstance(tags, list):
        sanitized["tags"] = _sanitize_tags(tags)

    return SanitizedExternalItem(item=sanitized)


def _validate_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("External source endpoint must use http/https.")
    if not parsed.netloc:
        raise ValueError("External source endpoint must include a host.")


def _sanitize_text(value: str) -> str:
    cleaned = value.replace("\x00", "").strip()
    if len(cleaned) > MAX_TEXT_FIELD_LENGTH:
        return cleaned[:MAX_TEXT_FIELD_LENGTH]
    return cleaned


def _sanitize_list(value: list[Any]) -> list[Any]:
    result: list[Any] = []
    for item in value:
        if isinstance(item, str):
            result.append(_sanitize_text(item))
        elif isinstance(item, dict):
            result.append(_sanitize_dict(item))
        elif isinstance(item, list):
            result.append(_sanitize_list(item))
        else:
            result.append(item)
    return result


def _sanitize_dict(value: dict[Any, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        normalized_key = str(key).strip()
        if not normalized_key:
            continue
        if isinstance(item, str):
            result[normalized_key] = _sanitize_text(item)
        elif isinstance(item, dict):
            result[normalized_key] = _sanitize_dict(item)
        elif isinstance(item, list):
            result[normalized_key] = _sanitize_list(item)
        else:
            result[normalized_key] = item
    return result


def _sanitize_tags(tags: list[Any]) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        cleaned = _sanitize_text(str(tag)).lower()
        if not cleaned:
            continue
        if len(cleaned) > MAX_TAG_LENGTH:
            cleaned = cleaned[:MAX_TAG_LENGTH]
        normalized.append(cleaned)
    deduplicated = []
    seen: set[str] = set()
    for item in normalized:
        if item in seen:
            continue
        seen.add(item)
        deduplicated.append(item)
    return deduplicated[:MAX_TAGS]
